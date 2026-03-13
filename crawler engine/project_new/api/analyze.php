<?php
// api/analyze.php
declare(strict_types=1);

require __DIR__ . '/_bootstrap.php';
// require_login();

/**
 * 一律回 JSON，避免任何 warning/notice 混成 HTML
 */
header('Content-Type: application/json; charset=utf-8');
error_reporting(0);
ini_set('display_errors', '0');

function json_out(array $data, int $code = 200): void {
  http_response_code($code);
  echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

function r(int $min, int $max): int {
  return random_int($min, $max);
}

/**
 * 讀取 metrics_json：
 * - 支援 FormData: $_POST['metrics_json']
 * - 支援 JSON body: php://input（Content-Type: application/json）
 */
function read_metrics_payload(): ?array {
  // 1) FormData
  if (!empty($_POST['metrics_json'])) {
    $m = json_decode((string)$_POST['metrics_json'], true);
    return is_array($m) ? $m : null;
  }

  // 2) JSON body
  $raw = file_get_contents('php://input');
  if (!$raw) return null;

  $body = json_decode($raw, true);
  if (!is_array($body)) return null;

  // 允許 body 直接就是 metrics，也允許包在 metrics_json 欄位
  if (isset($body['metrics_json']) && is_string($body['metrics_json'])) {
    $m = json_decode($body['metrics_json'], true);
    return is_array($m) ? $m : null;
  }

  // 如果 body 本身就含 blendshapes/landmarks
  if (isset($body['blendshapes']) || isset($body['landmarks'])) {
    return $body;
  }

  return null;
}

/**
 * 嘗試從 metrics 裡面拿 blendshapes（52 分數）
 * 回傳: name => score 的 map
 */
function blend_map(?array $metrics): array {
  if (!$metrics) return [];

  $blend = $metrics['blendshapes'] ?? null;
  if (!is_array($blend)) return [];

  $map = [];
  foreach ($blend as $item) {
    if (!is_array($item)) continue;
    $name = $item['name'] ?? $item['categoryName'] ?? null;
    $score = $item['score'] ?? null;
    if (!is_string($name)) continue;
    $map[$name] = is_numeric($score) ? (float)$score : 0.0;
  }
  return $map;
}

/**
 * 從 blendshape map 算出你的五項指標（0~100）
 * 這只是示範權重，你可以自己調整/替換
 */
function metrics_from_blend(array $b): ?array {
  if (!$b) return null;

  $smile = (($b['mouthSmileLeft'] ?? 0) + ($b['mouthSmileRight'] ?? 0)) / 2;
  $frown = (($b['mouthFrownLeft'] ?? 0) + ($b['mouthFrownRight'] ?? 0)) / 2;
  $blink = (($b['eyeBlinkLeft'] ?? 0) + ($b['eyeBlinkRight'] ?? 0)) / 2;
  $jawOpen = ($b['jawOpen'] ?? 0);
  $browUp = ($b['browInnerUp'] ?? 0);

  // 把 0~1 轉成 0~100（並簡單做反向）
  $glow       = clamp100((1 - $blink) * 100);     // 眨眼多可能偵測不穩（示意）
  $complexion = clamp100(($smile) * 100);         // 微笑/表情放鬆（示意）
  $blemish    = clamp100((1 - $frown) * 100);     // 皺眉/不適（示意）
  $oilBalance = clamp100((1 - $jawOpen) * 100);   // 張嘴大（示意）
  $evenness   = clamp100(($browUp) * 100);        // 抬眉（示意）

  return [
    'glow'       => (int)round($glow),
    'complexion' => (int)round($complexion),
    'blemish'    => (int)round($blemish),
    'oilBalance' => (int)round($oilBalance),
    'evenness'   => (int)round($evenness),
  ];
}

function clamp100(float $x): float {
  if ($x < 0) return 0;
  if ($x > 100) return 100;
  return $x;
}

// --------------------
// 讀取「數值資料」：可有可無
// --------------------
$metricsPayload = read_metrics_payload();
$blendMap = blend_map($metricsPayload);

// --------------------
// 讀取「照片」：可選（如果只想即時送數值，就不一定要 photo）
// --------------------
$photoUrl = null;
$payloadId = bin2hex(random_bytes(8));

if (isset($_FILES['photo']) && is_array($_FILES['photo'])) {
  $up = $_FILES['photo'];
  if (($up['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) {
    json_out(['ok' => false, 'error' => 'upload error'], 400);
  }

  // MIME 檢查
  $finfo = finfo_open(FILEINFO_MIME_TYPE);
  $mime = $finfo ? finfo_file($finfo, $up['tmp_name']) : '';
  if ($finfo) finfo_close($finfo);

  $allowed = ['image/jpeg', 'image/png', 'image/webp'];
  if (!in_array($mime, $allowed, true)) {
    json_out(['ok' => false, 'error' => 'invalid file type', 'mime' => $mime], 400);
  }

  // uploads dir
  $uploadsPath = realpath(__DIR__ . '/../uploads');
  if ($uploadsPath === false) {
    $target = __DIR__ . '/../uploads';
    @mkdir($target, 0777, true);
    $uploadsPath = realpath($target);
  }
  if ($uploadsPath === false) {
    json_out(['ok' => false, 'error' => 'cannot create uploads dir'], 500);
  }

  // 存檔
  $ext = 'jpg';
  if ($mime === 'image/png') $ext = 'png';
  if ($mime === 'image/webp') $ext = 'webp';

  $filename = 'cap_' . date('Ymd_His') . '_' . $payloadId . '.' . $ext;
  $dest = $uploadsPath . DIRECTORY_SEPARATOR . $filename;

  if (!move_uploaded_file($up['tmp_name'], $dest)) {
    json_out(['ok' => false, 'error' => 'move failed'], 500);
  }

  $photoUrl = 'uploads/' . $filename;
} else {
  // 如果你希望「一定要有照片」才分析，就把下面打開：
  // json_out(['ok' => false, 'error' => 'missing photo'], 400);
}

// --------------------
// 產生「前端吃得下」的 metrics
// - 若收到 blendshapes => 用它算（示意）
// - 否則用 random mock（維持你原本行為）
// --------------------
$metrics = metrics_from_blend($blendMap);
if (!$metrics) {
  $metrics = [
    'glow'       => r(55, 95),
    'complexion' => r(50, 95),
    'blemish'    => r(40, 90),
    'oilBalance' => r(45, 90),
    'evenness'   => r(50, 95),
  ];
}

$overall = (int) round(array_sum($metrics) / count($metrics));

$tag =
  $overall >= 85 ? '狀態極佳' :
  ($overall >= 75 ? '整體良好' :
  ($overall >= 60 ? '可再提升' : '需要加強'));

$skinType =
  ($metrics['oilBalance'] < 55 && $metrics['evenness'] < 60) ? '偏乾 / 缺水型' :
  ($metrics['oilBalance'] < 55 ? '混合偏油' : '偏穩定');

$summary =
  $overall >= 75
    ? '氣色與膚況整體穩定，維持作息與補水，亮度會更明顯。'
    : ($overall >= 60
        ? '整體不錯但仍有可加強點，先把保濕與防曬做穩，改善會很快。'
        : '目前狀態偏疲態或膚況不穩，建議先從睡眠、清潔、保濕打底。');

$tips = [];
if ($metrics['complexion'] < 60) $tips[] = '氣色偏低：建議自然光下重拍，並確認睡眠與飲水。';
if ($metrics['blemish'] < 55)    $tips[] = '瑕疵指標偏低：先把溫和清潔＋保濕做穩，避免刺激性保養。';
if ($metrics['oilBalance'] < 55) $tips[] = '油水平衡偏低：可能過乾或過油，建議簡化保養並觀察 3–7 天。';
if ($metrics['glow'] < 60)       $tips[] = '光澤偏低：避免背光與強反光，採自然側光更準確。';
if ($metrics['evenness'] < 60)   $tips[] = '均勻度偏低：防曬與減少摩擦，通常是提升關鍵。';

if (count($tips) === 0) {
  $tips = [
    '目前沒有明顯弱項：維持作息＋防曬習慣即可。',
    '同時間連續拍 3 天，比單次結果更可信。',
  ];
}

$products = [
  [
    'name' => '溫和潔面',
    'desc' => '低刺激、日常清潔用，避免過度清潔造成乾燥。',
    'tag'  => '基礎清潔',
    'url'  => '#',
  ],
  [
    'name' => '保濕精華',
    'desc' => '補水打底，改善乾燥與粗糙感。',
    'tag'  => '補水修護',
    'url'  => '#',
  ],
  [
    'name' => '清爽乳液',
    'desc' => '油水平衡與鎖水兼顧，適合混合/油性肌。',
    'tag'  => '清爽保濕',
    'url'  => '#',
  ],
];

// 回傳（加上 debug 讓你確定有收到數值）
json_out([
  'ok'           => true,
  'payload_id'   => $payloadId,
  'generated_at' => date('c'),
  'photo_url'    => $photoUrl,
  'overall'      => $overall,
  'tag'          => $tag,
  'skinType'     => $skinType,
  'summary'      => $summary,
  'metrics'      => $metrics,
  'tips'         => $tips,
  'products'     => $products,

  // ✅ 這兩個是你確認「我真的有收到」用的
  'received' => [
    'has_photo' => $photoUrl !== null,
    'has_metrics' => $metricsPayload !== null,
    'blendshape_count' => count($blendMap),
  ],
]);
