const http = require('http');
const fs   = require('fs');
const path = require('path');

const PORT = 3002;
const FILE = path.join(__dirname, 'index.html');

http.createServer((req, res) => {
  const content = fs.readFileSync(FILE);
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(content);
}).listen(PORT, () => {
  console.log(`\n  Atelier Mobile  →  http://localhost:${PORT}\n`);
});
