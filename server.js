const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8080;

const server = http.createServer((req, res) => {
    // 루트 경로로 접근하면 index.html 반환
    let filePath = req.url === '/' ? '/index.html' : req.url;
    filePath = path.join(__dirname, filePath);

    fs.readFile(filePath, 'utf-8', (err, data) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
            res.end('<h1>404 - 파일을 찾을 수 없습니다</h1>');
        } else {
            // 파일 확장자에 따라 Content-Type 설정
            const ext = path.extname(filePath);
            let contentType = 'text/html; charset=utf-8';
            
            if (ext === '.css') contentType = 'text/css; charset=utf-8';
            if (ext === '.js') contentType = 'application/javascript; charset=utf-8';
            
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(data);
        }
    });
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`🚀 웹 서버가 실행 중입니다!`);
    console.log(`📍 로컬 주소: http://localhost:${PORT}`);
    console.log(`📍 또는: http://127.0.0.1:${PORT}`);
    console.log(`\n도메인으로 접근하려면 hosts 파일을 수정해야 합니다.`);
    console.log(`Windows: C:\\Windows\\System32\\drivers\\etc\\hosts`);
    console.log(`다음 줄을 추가하세요:`);
    console.log(`127.0.0.1 unrealnew.unrealnew.com`);
});
