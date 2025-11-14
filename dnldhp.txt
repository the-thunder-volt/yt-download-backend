<?php
// ===============================
// 1️⃣ Allow React requests (CORS)
// ===============================
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// ===============================
// 2️⃣ Get video URL
// ===============================
if (!isset($_POST['url']) || empty($_POST['url'])) {
    http_response_code(400);
    echo json_encode(["error" => "No URL provided"]);
    exit();
}

$url = escapeshellarg($_POST['url']);
$filename = "video_" . time() . ".mp4";
$outputPath = __DIR__ . DIRECTORY_SEPARATOR . $filename;

// ===============================
// 3️⃣ Run yt-dlp command
// ===============================
$command = "yt-dlp -f \"bv*+ba/b\" -o " . escapeshellarg($outputPath) . " $url";
exec($command, $output, $status);

// ===============================
// 4️⃣ Check if download worked
// ===============================
if ($status !== 0 || !file_exists($outputPath)) {
    http_response_code(500);
    echo json_encode(["error" => "Download failed", "details" => $output]);
    exit();
}

// ===============================
// 5️⃣ Stream back the file
// ===============================
header("Content-Type: video/mp4");
header("Content-Disposition: attachment; filename=\"video.mp4\"");
header("Content-Length: " . filesize($outputPath));
readfile($outputPath);

// Cleanup
unlink($outputPath);
exit();
?>
<!-- php -S localhost:8000 -->
