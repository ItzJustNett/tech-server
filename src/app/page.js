// page.js

"use client";

import { useEffect, useRef, useState } from 'react';

export default function Home() {
  const canvasRef = useRef(null);
  const [scrolled, setScrolled] = useState(false);

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
    const trailTimeout = 1000; // 1 second before trails disappear
    
    const createShootingStar = () => {
      const x = Math.random() * canvas.width;
      const y = Math.random() * (canvas.height/3);
      const newStar = {
        x,
        y,
        length: Math.random() * 80 + 50,
        speed: Math.random() * 10 + 10,
        angle: Math.random() * Math.PI / 4 + Math.PI / 4,
        life: 1,
        decay: Math.random() * 0.02 + 0.01,
        trail: [],
        shouldDrawTrail: true
      };
      
      shootingStars.push(newStar);
      
      // Set timeout to remove the trail after a few seconds
      setTimeout(() => {
        if (shootingStars.includes(newStar)) {
          newStar.shouldDrawTrail = false;
        }
      }, trailTimeout);
    };
    
    // Animation
    const animate = () => {
      // Clear canvas with a solid dark background
      ctx.fillStyle = 'rgba(0, 0, 10, 0.1)';
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
        // Draw star head
        ctx.beginPath();
        ctx.fillStyle = `rgba(255, 255, 255, ${star.life})`;
        ctx.arc(star.x, star.y, 1.5, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw star trail if enabled
        if (star.shouldDrawTrail) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(255, 255, 255, ${star.life})`;
          ctx.lineWidth = 2;
          
          // Calculate trail end position
          const x2 = star.x + Math.cos(star.angle + Math.PI) * star.length;
          const y2 = star.y + Math.sin(star.angle + Math.PI) * star.length;
          
          // Draw trail
          ctx.moveTo(star.x, star.y);
          ctx.lineTo(x2, y2);
          ctx.stroke();
        }
        
        // Store current position for trail
        star.trail.push({x: star.x, y: star.y});
        if (star.trail.length > 10) star.trail.shift();
        
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
    
    // Scroll handler
    const handleScroll = () => {
      if (window.scrollY > 100) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll);
    
    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return (
    <div id="main-container">
      <div id="sky-section">
        <canvas 
          ref={canvasRef} 
          id="nightSkyCanvas"
        />
        
        <div id="sky-content">
          <h1 id="title">Neon Mind</h1>
          <p id="quote">The future is now.</p>
          <div id="scroll-indicator">
            <div id="scroll-arrow">↓</div>
          </div>
        </div>
      </div>
      
      <div id="einstein-section">
        <div id="einstein-container">
          <p id="einstein-quote">
            <span className="quote-marks">"</span>Once you stop learning, you start dying.<span className="quote-marks">"</span>
            <br />
            <span id="quote-author">– Albert Einstein</span>
          </p>
          <div id="einstein-image-container">
            <img 
              src="https://hips.hearstapps.com/hmg-prod/images/albert-einstein-sticks-out-his-tongue-when-asked-by-news-photo-1681316749.jpg" 
              alt="Albert Einstein sticking out his tongue" 
              id="einstein-image"
            />
          </div>
        </div>
      </div>
      
      <style jsx global>{`
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        body {
          font-family: sans-serif;
          overflow-x: hidden;
          background-color: #000;
        }

        #main-container {
          width: 100%;
        }
        
        #sky-section {
          position: relative;
          width: 100vw;
          height: 100vh;
          background-color: #000;
        }
        
        #nightSkyCanvas {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 0;
        }
        
        #sky-content {
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
          color: #8a2be2;
          text-shadow: 0 0 10px #8a2be2,
                      0 0 20px #3399ff,
                      0 0 30px #8a2be2;
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
            text-shadow: 0 0 10px rgba(138, 43, 226, 0.5),
                        0 0 20px rgba(51, 153, 255, 0.5);
          }
          to {
            text-shadow: 0 0 15px rgba(138, 43, 226, 0.8),
                        0 0 25px rgba(51, 153, 255, 0.8),
                        0 0 35px rgba(138, 43, 226, 0.5);
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
        
        #scroll-indicator {
          position: absolute;
          bottom: 30px;
          left: 50%;
          transform: translateX(-50%);
          color: white;
          text-align: center;
          opacity: 0;
          animation: fadeIn 2s forwards 2s;
        }
        
        #scroll-arrow {
          font-size: 1.5rem;
          animation: bounce 2s infinite;
          color: rgba(138, 43, 226, 0.7);
          text-shadow: 0 0 5px rgba(138, 43, 226, 0.3);
        }
        
        @keyframes bounce {
          0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
          }
          40% {
            transform: translateY(-15px);
          }
          60% {
            transform: translateY(-7px);
          }
        }
        
        #einstein-section {
          min-height: 100vh;
          width: 100%;
          display: flex;
          justify-content: center;
          align-items: center;
          background-color: #000;
          padding: 2rem;
          position: relative;
          border-top: 1px solid rgba(138, 43, 226, 0.2);
        }
        
        #einstein-section::before {
          display: none;
        }
        
        #einstein-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          animation: fadeIn 1.5s ease-out;
        }
        
        #einstein-quote {
          font-size: 1.5rem;
          color: #ffffff;
          text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
          margin-bottom: 1.5rem;
          text-align: center;
          line-height: 1.6;
        }
        
        .quote-marks {
          color: #8a2be2;
          text-shadow: 0 0 5px rgba(138, 43, 226, 0.5);
          font-size: 1.8rem;
          font-weight: bold;
        }
        
        #quote-author {
          font-size: 1.2rem;
          font-style: italic;
          opacity: 0.9;
        }
        
        #einstein-image-container {
          width: 180px;
          height: 180px;
          border-radius: 50%;
          overflow: hidden;
          border: 3px solid #8a2be2;
          box-shadow: 0 0 15px rgba(138, 43, 226, 0.7), 
                      0 0 30px rgba(51, 153, 255, 0.5);
          animation: glowPulse 3s infinite alternate;
        }
        
        #einstein-image {
          width: 100%;
          height: 100%;
          object-fit: cover;
          transform: scale(1.1);
        }
        
        @keyframes glowPulse {
          from {
            box-shadow: 0 0 15px rgba(138, 43, 226, 0.7), 
                        0 0 30px rgba(51, 153, 255, 0.5);
          }
          to {
            box-shadow: 0 0 20px rgba(138, 43, 226, 0.9), 
                        0 0 40px rgba(51, 153, 255, 0.7);
          }
        }
      `}
      </style>
    </div>
  );
}
