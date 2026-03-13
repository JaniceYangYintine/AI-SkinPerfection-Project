<?php
declare(strict_types=1);
session_start();

header('X-Content-Type-Options: nosniff');

if (!function_exists('json_out')) {
  function json_out($data, int $code=200): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
  }
}

// function require_login(): void {
//   if (!isset($_SESSION['user'])) {
//     http_response_code(401);
//     exit("Not logged in");
//   }
// }
