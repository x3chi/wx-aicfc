// static/wave.js

const wavePath = document.getElementById("wavePath");
let t = 0;

function generateWavePath(amplitude = 20, frequency = 0.01, offset = 100) {
  const width = 1200;
  const height = 200;
  let path = `M0 ${height} `;

  for (let x = 0; x <= width; x += 10) {
    const y = Math.sin((x + t) * frequency) * amplitude + offset;
    path += `L${x} ${y} `;
  }

  path += `L${width} ${height} L0 ${height} Z`;
  return path;
}

function animateWave() {
  wavePath.setAttribute("d", generateWavePath());
  t += 2;
  requestAnimationFrame(animateWave);
}

animateWave();
