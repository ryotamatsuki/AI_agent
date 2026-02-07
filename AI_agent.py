import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Mini Platformer", page_icon="🍄", layout="centered")

st.title("🍄 ちいさなマリオ風プラットフォーマー")
st.write(
    "矢印キーで左右に移動、スペースキーでジャンプ。ゴールの旗に触れるとクリアです。"
)

GAME_HTML = """
<!DOCTYPE html>
<html lang=\"ja\">
<head>
  <meta charset=\"UTF-8\" />
  <style>
    body { margin: 0; background: #9bd3ff; font-family: sans-serif; }
    #game { background: linear-gradient(#9bd3ff 0%, #dff6ff 60%, #9ad07f 60%); display: block; margin: 0 auto; border: 4px solid #2b2b2b; }
    #hud { text-align: center; padding: 8px; font-weight: bold; }
  </style>
</head>
<body>
  <div id=\"hud\">←/→ で移動、Spaceでジャンプ</div>
  <canvas id=\"game\" width=\"800\" height=\"400\"></canvas>

  <script>
    const canvas = document.getElementById('game');
    const ctx = canvas.getContext('2d');

    const gravity = 0.6;
    const friction = 0.8;
    const player = {
      x: 50,
      y: 280,
      w: 32,
      h: 40,
      vx: 0,
      vy: 0,
      speed: 0.6,
      jump: -12,
      grounded: false
    };

    const platforms = [
      { x: 0, y: 320, w: 800, h: 80 },
      { x: 120, y: 250, w: 120, h: 20 },
      { x: 320, y: 210, w: 140, h: 20 },
      { x: 520, y: 170, w: 120, h: 20 },
      { x: 680, y: 260, w: 80, h: 20 }
    ];

    const flag = { x: 740, y: 110, w: 20, h: 90 };

    const keys = { left: false, right: false, jump: false };
    let cleared = false;

    function handleKeyDown(e) {
      if (e.code === 'ArrowLeft') keys.left = true;
      if (e.code === 'ArrowRight') keys.right = true;
      if (e.code === 'Space') keys.jump = true;
    }

    function handleKeyUp(e) {
      if (e.code === 'ArrowLeft') keys.left = false;
      if (e.code === 'ArrowRight') keys.right = false;
      if (e.code === 'Space') keys.jump = false;
    }

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    function update() {
      if (keys.left) player.vx -= player.speed;
      if (keys.right) player.vx += player.speed;

      if (keys.jump && player.grounded) {
        player.vy = player.jump;
        player.grounded = false;
      }

      player.vx *= friction;
      player.vy += gravity;
      player.x += player.vx;
      player.y += player.vy;

      if (player.x < 0) player.x = 0;
      if (player.x + player.w > canvas.width) player.x = canvas.width - player.w;

      player.grounded = false;
      platforms.forEach((p) => {
        const collideX = player.x < p.x + p.w && player.x + player.w > p.x;
        const collideY = player.y < p.y + p.h && player.y + player.h > p.y;
        if (collideX && collideY) {
          const prevY = player.y - player.vy;
          if (prevY + player.h <= p.y) {
            player.y = p.y - player.h;
            player.vy = 0;
            player.grounded = true;
          } else if (prevY >= p.y + p.h) {
            player.y = p.y + p.h;
            player.vy = 0;
          } else if (player.x + player.w / 2 < p.x + p.w / 2) {
            player.x = p.x - player.w;
            player.vx = 0;
          } else {
            player.x = p.x + p.w;
            player.vx = 0;
          }
        }
      });

      if (
        player.x < flag.x + flag.w &&
        player.x + player.w > flag.x &&
        player.y < flag.y + flag.h &&
        player.y + player.h > flag.y
      ) {
        cleared = true;
      }
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      platforms.forEach((p) => {
        ctx.fillStyle = '#3c7a2c';
        ctx.fillRect(p.x, p.y, p.w, p.h);
        ctx.fillStyle = '#2b5720';
        ctx.fillRect(p.x, p.y, p.w, 6);
      });

      ctx.fillStyle = '#f4d03f';
      ctx.fillRect(flag.x, flag.y, 6, flag.h);
      ctx.fillStyle = '#ff4757';
      ctx.beginPath();
      ctx.moveTo(flag.x + 6, flag.y + 10);
      ctx.lineTo(flag.x + 6 + flag.w, flag.y + 25);
      ctx.lineTo(flag.x + 6, flag.y + 40);
      ctx.closePath();
      ctx.fill();

      ctx.fillStyle = '#ff6b6b';
      ctx.fillRect(player.x, player.y, player.w, player.h);
      ctx.fillStyle = '#2b2b2b';
      ctx.fillRect(player.x + 6, player.y + 12, 6, 6);
      ctx.fillRect(player.x + 20, player.y + 12, 6, 6);

      if (cleared) {
        ctx.fillStyle = 'rgba(0,0,0,0.6)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ffffff';
        ctx.font = '32px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('CLEAR! おめでとう！', canvas.width / 2, canvas.height / 2);
        ctx.font = '16px sans-serif';
        ctx.fillText('リロードで再スタート', canvas.width / 2, canvas.height / 2 + 30);
      }
    }

    function loop() {
      if (!cleared) {
        update();
      }
      draw();
      requestAnimationFrame(loop);
    }

    loop();
  </script>
</body>
</html>
"""

components.html(GAME_HTML, height=460)

st.caption("ブラウザのフォーカスが外れているとキー操作が効かないので、ゲーム画面をクリックしてから操作してください。")
