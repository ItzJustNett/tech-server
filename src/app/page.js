// page.js

"use client";

import { useEffect, useRef } from 'react';

export default function Home() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const stars = [];
    
    // Set canvas to full screen
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Create stars
    for (let i = 0; i < 200; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 1.5,
        opacity: Math.random(),
        speed: Math.random() * 0.05
      });
    }
    
    // Create shooting stars
    const shootingStars = [];
    const createShootingStar = () => {
      const x = Math.random() * canvas.width;
      const y = Math.random() * (canvas.height/3);
      shootingStars.push({
        x,
        y,
        length: Math.random() * 80 + 50,
        speed: Math.random() * 10 + 10,
        angle: Math.random() * Math.PI / 4 + Math.PI / 4,
        life: 1,
        decay: Math.random() * 0.02 + 0.01
      });
    };
    
    // Animation
    const animate = () => {
      // Clear canvas
      ctx.fillStyle = 'rgba(10, 10, 30, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw stars
      stars.forEach(star => {
        ctx.beginPath();
        
        // Create twinkling effect
        star.opacity += Math.random() * 0.01 - 0.005;
        star.opacity = Math.max(0, Math.min(1, star.opacity));
        
        ctx.fillStyle = `rgba(255, 255, 255, ${star.opacity})`;
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fill();
        
        // Slight movement
        star.y += star.speed;
        
        // Reset if off screen
        if (star.y > canvas.height) {
          star.y = 0;
          star.x = Math.random() * canvas.width;
        }
      });
      
      // Draw shooting stars
      shootingStars.forEach((star, index) => {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(255, 255, 255, ${star.life})`;
        ctx.lineWidth = 2;
        
        // Calculate position
        const x2 = star.x + Math.cos(star.angle) * star.length;
        const y2 = star.y + Math.sin(star.angle) * star.length;
        
        // Draw line
        ctx.moveTo(star.x, star.y);
        ctx.lineTo(x2, y2);
        ctx.stroke();
        
        // Move shooting star
        star.x += Math.cos(star.angle) * star.speed;
        star.y += Math.sin(star.angle) * star.speed;
        
        // Fade out
        star.life -= star.decay;
        
        // Remove if invisible
        if (star.life <= 0 || star.x > canvas.width || star.y > canvas.height) {
          shootingStars.splice(index, 1);
        }
      });
      
      // Random chance to create new shooting star
      if (Math.random() < 0.01 && shootingStars.length < 3) {
        createShootingStar();
      }
      
      requestAnimationFrame(animate);
    };
    
    animate();
    
    // Resize handler
    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div id="nightSkyContainer">
      <canvas 
        ref={canvasRef} 
        id="nightSkyCanvas"
      />
      
      <div id="content">
        <h1 id="title">Neon Mind</h1>
        <p id="quote">The future is now.</p>
      </div>
      
      <style jsx global>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        body {
          font-family: sans-serif;
          overflow: hidden;
        }

        #nightSkyContainer {
          position: relative;
          width: 100vw;
          height: 100vh;
          overflow: hidden;
          background: linear-gradient(to bottom, #0a0a2e, #1a1a4a);
        }
        
        #nightSkyCanvas {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        
        #content {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          z-index: 10;
        }
        
        #title {
          font-size: 5rem;
          font-weight: bold;
          margin-bottom: 1rem;
          color: #ff00cc;
          text-shadow: 0 0 10px #ff00cc,
                      0 0 20px #3399ff,
                      0 0 30px #ff00cc;
          animation: neonPulse 2s infinite alternate;
        }
        
        #quote {
          font-size: 1.5rem;
          color: #ffffff;
          text-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
          opacity: 0;
          animation: fadeIn 2s forwards 1s;
        }
        
        @keyframes neonPulse {
          from {
            text-shadow: 0 0 10px rgba(255, 0, 204, 0.5),
                        0 0 20px rgba(51, 153, 255, 0.5);
          }
          to {
            text-shadow: 0 0 15px rgba(255, 0, 204, 0.8),
                        0 0 25px rgba(51, 153, 255, 0.8),
                        0 0 35px rgba(255, 0, 204, 0.5);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}
      </style>
    </div>
  );
}
