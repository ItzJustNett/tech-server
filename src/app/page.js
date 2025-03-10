'use client';

import { useState, useEffect, useRef } from 'react';

export default function LearningAppPage() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [activeSection, setActiveSection] = useState('hero');
  
  const heroRef = useRef(null);
  const featuresRef = useRef(null);
  const statsRef = useRef(null);
  const testimonialRef = useRef(null);
  const ctaRef = useRef(null);
  
  // Parallax effect but with fixed elements to prevent glitching
  const [hasLoaded, setHasLoaded] = useState(false);
  
  // Set a fixed state after initial load
  useEffect(() => {
    if (isLoaded) {
      const timer = setTimeout(() => setHasLoaded(true), 100);
      return () => clearTimeout(timer);
    }
  }, [isLoaded]);
  
  // Handle scroll events for section detection only, not for animations
  useEffect(() => {
    // Throttle function to limit how often the scroll handler fires
    const throttle = (func, limit) => {
      let inThrottle;
      return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
          func.apply(context, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    };
    
    const handleScroll = throttle(() => {
      // Determine which section is currently in view
      const sections = [
        { ref: heroRef, id: 'hero' },
        { ref: featuresRef, id: 'features' },
        { ref: statsRef, id: 'stats' },
        { ref: testimonialRef, id: 'testimonial' },
        { ref: ctaRef, id: 'cta' }
      ];
      
      for (const section of sections) {
        if (section.ref.current) {
          const rect = section.ref.current.getBoundingClientRect();
          if (rect.top <= window.innerHeight / 2 && rect.bottom >= window.innerHeight / 2) {
            if (activeSection !== section.id) {
              setActiveSection(section.id);
            }
            break;
          }
        }
      }
    }, 200); // Increased threshold
    
    window.addEventListener('scroll', handleScroll);
    // Run once on initial render to set the initial active section
    handleScroll();
    
    return () => window.removeEventListener('scroll', handleScroll);
  }, [activeSection]);
  
  // Mock data
  const features = [
    { id: 1, title: "Adaptive Learning", description: "AI-powered system that adapts to your learning style", icon: "📚" },
    { id: 2, title: "Immersive Content", description: "Engaging 3D visualizations that bring concepts to life", icon: "🔮" },
    { id: 3, title: "Focus Sessions", description: "Science-backed learning intervals for maximum retention", icon: "⏱️" },
    { id: 4, title: "Global Community", description: "Connect with millions of learners worldwide", icon: "🌎" },
  ];

  const stats = [
    { id: 1, value: "94%", label: "Completion Rate" },
    { id: 2, value: "12M+", label: "Active Learners" },
    { id: 3, value: "189", label: "Countries" },
  ];

  // Stats counter animation
  const StatsCounter = ({ targetValue }) => {
    const [count, setCount] = useState(0);
    const counterRef = useRef(null);
    
    useEffect(() => {
      if (activeSection !== 'stats') {
        setCount(0);
        return;
      }
      
      // Parse the target value
      let endValue = parseInt(targetValue.replace(/[^0-9]/g, ''));
      if (isNaN(endValue)) endValue = 0;
      
      // Reset count when section changes
      if (count >= endValue) return;
      
      const duration = 2000; // ms
      const frameDuration = 1000 / 60; // 60fps
      const totalFrames = Math.round(duration / frameDuration);
      const counterIncrement = endValue / totalFrames;
      
      let frame = 0;
      const counter = setInterval(() => {
        frame++;
        const newCount = Math.min(Math.ceil(counterIncrement * frame), endValue);
        setCount(newCount);
        
        if (frame === totalFrames) {
          clearInterval(counter);
        }
      }, frameDuration);
      
      return () => clearInterval(counter);
    }, [activeSection, targetValue, count]);
    
    // For values with "+" or other characters
    const suffix = targetValue.replace(/[0-9]/g, '');
    
    return <span>{count}{suffix}</span>;
  };

  // Simulate loading
  useEffect(() => {
    const timer = setTimeout(() => setIsLoaded(true), 800);
    return () => clearTimeout(timer);
  }, []);

  if (!isLoaded) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: 'linear-gradient(to bottom, #000428, #001e54, #000428)' }}>
        <div className="w-16 h-16 border-t-4 border-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative text-white">
      {/* Fixed position star background */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none" style={{ background: 'linear-gradient(to bottom, #000428, #001e54, #000428)' }}>
        <div className="absolute inset-0">
          {Array.from({ length: 200 }).map((_, i) => {
            const size = Math.random() * 1.5; // Smaller size range for stars
            const opacity = Math.random() * 0.5 + 0.1; // Varied opacity
            return (
              <div
                key={i}
                className="absolute rounded-full"
                style={{
                  width: `${size}px`,
                  height: `${size}px`,
                  backgroundColor: i % 5 === 0 ? '#FFF5F0' : i % 3 === 0 ? '#FFFFFF' : '#E3E3FF',
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  opacity: opacity,
                  boxShadow: `0 0 ${Math.random() * 3 + 1}px rgba(255, 255, 255, ${opacity})`,
                  animation: 'starTwinkle 4s infinite alternate',
                  animationDelay: `${Math.random() * 10}s`,
                  animationDuration: `${Math.random() * 3 + 3}s`
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Hero Section */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center px-4 z-10"
      >
        <div className="max-w-6xl mx-auto text-center">
          <div className={`transition-all duration-1000 ${activeSection === 'hero' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 text-transparent bg-clip-text">
              Learn Like Never Before
            </h1>
            <p className="text-xl md:text-2xl text-gray-300 mb-10 max-w-3xl mx-auto">
              The most advanced learning platform powered by artificial intelligence.
              Master any skill at your own pace with personalized guidance.
            </p>
          </div>

          <div className={`relative w-full max-w-3xl mx-auto aspect-video rounded-2xl overflow-hidden transition-all duration-1000 ${activeSection === 'hero' ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
            <div className="absolute inset-0 border border-blue-500/20 z-10 rounded-2xl" />
            <div className="absolute inset-0 backdrop-blur-sm z-0 rounded-2xl animate-pulse shadow-lg" 
                 style={{ animationDuration: '5s' }} />
            <div className="absolute inset-0 flex items-center justify-center z-20">
              <div className="w-64 h-64 backdrop-blur-sm rounded-3xl p-4 flex flex-col items-center justify-center transform rotate-12 shadow-xl border border-blue-500/20">
                <div className="w-full h-2 bg-blue-500/30 rounded-full mb-4" />
                <div className="grid grid-cols-3 gap-2 w-full">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div 
                      key={i}
                      className="backdrop-blur-sm border border-blue-500/30 aspect-square rounded-lg flex items-center justify-center animate-pulse"
                      style={{ animationDuration: '2s', animationDelay: `${i * 0.2}s` }}
                    >
                      <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-400 to-purple-500" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className={`mt-12 transition-all duration-1000 ${activeSection === 'hero' ? 'opacity-100' : 'opacity-0'}`}>
            <button className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full text-lg font-bold tracking-wide transform transition-transform hover:scale-105">
              Download Now
            </button>
            <p className="mt-4 text-gray-400">Available on iOS and Android</p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section
        ref={featuresRef}
        className="relative py-24 z-10"
      >
        <div className={`max-w-6xl mx-auto px-4 transition-all duration-1000 ${activeSection === 'features' ? 'opacity-100' : 'opacity-50'}`}>
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16 bg-gradient-to-r from-blue-400 to-purple-600 text-transparent bg-clip-text">
            Revolutionary Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 px-4">
            {features.map((feature, index) => (
              <div
                key={feature.id}
                className={`p-8 rounded-2xl backdrop-blur-lg transition-all duration-700 border border-blue-500/20 ${
                  activeSection === 'features' 
                    ? 'opacity-100 translate-y-0' 
                    : 'opacity-0 translate-y-12'
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div
                  className="text-4xl mb-4"
                >
                  {feature.icon}
                </div>
                <h3 className="text-2xl font-bold mb-2 text-blue-300">{feature.title}</h3>
                <p className="text-gray-300">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section
        ref={statsRef}
        className="relative py-24 z-10"
      >
        <div className="max-w-6xl mx-auto px-4">
          <div className={`grid grid-cols-1 md:grid-cols-3 gap-8 transition-all duration-1000 ${
            activeSection === 'stats' ? 'opacity-100' : 'opacity-50'
          }`}>
            {stats.map((stat, index) => (
              <div
                key={stat.id}
                className={`text-center transition-all duration-700 ${
                  activeSection === 'stats' 
                    ? 'opacity-100 scale-100' 
                    : 'opacity-0 scale-90'
                }`}
                style={{ transitionDelay: `${index * 200}ms` }}
              >
                <div className="text-5xl md:text-6xl font-bold text-blue-400 mb-2" ref={el => el}>
                  {activeSection === 'stats' ? <StatsCounter targetValue={stat.value} /> : "0"}
                </div>
                <p className="text-lg text-gray-300">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonial Section */}
      <section
        ref={testimonialRef}
        className="relative py-24 z-10"
      >
        <div className="max-w-4xl mx-auto px-4">
          <div className={`text-center transition-all duration-1000 ${
            activeSection === 'testimonial' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
          }`}>
            <h2 className="text-4xl md:text-5xl font-bold mb-16 bg-gradient-to-r from-blue-400 to-purple-600 text-transparent bg-clip-text">
              What Our Users Say
            </h2>
          </div>

          <div className={`p-10 rounded-3xl backdrop-blur-lg relative overflow-hidden transition-all duration-1000 shadow-lg border border-blue-500/20 ${
            activeSection === 'testimonial' ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
          }`} style={{ transitionDelay: '300ms' }}>
            <div
              className="absolute inset-0 opacity-10 bg-pattern-dots"
              style={{
                backgroundImage: 'url("/api/placeholder/400/400")', 
                backgroundSize: '400px 400px',
                animation: 'backgroundMove 20s linear infinite alternate'
              }}
            />
            
            <div className="relative z-10">
              <p className="text-xl md:text-2xl italic mb-8 text-gray-200">
                "This app completely transformed how I learn. The adaptive AI understands exactly
                what I need and when I need it. I've learned more in 2 months than I did in 2 years
                of traditional study."
              </p>
              
              <div className="flex items-center justify-center">
                <div className="w-14 h-14 rounded-full bg-gradient-to-r from-blue-400 to-purple-500 p-0.5 shadow-lg shadow-blue-500/20">
                  <div className="w-full h-full rounded-full backdrop-blur-sm flex items-center justify-center text-2xl">
                    👩‍💻
                  </div>
                </div>
                <div className="ml-4 text-left">
                  <p className="font-bold">Sarah Johnson</p>
                  <p className="text-gray-400 text-sm">Software Engineer</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section
        ref={ctaRef}
        className="relative py-24 z-10"
      >
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className={`transition-all duration-1000 ${
            activeSection === 'cta' ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'
          }`}>
            <h2 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-600 text-transparent bg-clip-text">
              Start Your Learning Journey Today
            </h2>
            <p className="text-xl text-gray-300 mb-12 max-w-3xl mx-auto">
              Join millions of learners worldwide and unlock your full potential.
              The future of education is here.
            </p>
          </div>

          <div className={`flex flex-col sm:flex-row items-center justify-center gap-6 transition-all duration-1000 ${
            activeSection === 'cta' ? 'opacity-100 scale-100' : 'opacity-0 scale-90'
          }`} style={{ transitionDelay: '300ms' }}>
            <button className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full text-lg font-bold tracking-wide transform transition-transform hover:scale-105 w-full sm:w-auto">
              Download Now
            </button>
            <button className="px-8 py-4 bg-transparent border-2 border-blue-400 rounded-full text-lg font-bold tracking-wide transform transition-transform hover:scale-105 w-full sm:w-auto">
              Watch Demo
            </button>
          </div>

          <div className={`mt-12 text-gray-400 transition-all duration-1000 ${
            activeSection === 'cta' ? 'opacity-100' : 'opacity-0'
          }`} style={{ transitionDelay: '600ms' }}>
            <p>No credit card required • Free 7-day trial • Cancel anytime</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 text-blue-200/60 text-center text-sm relative z-10 border-t border-blue-500/20">
        <div className="max-w-6xl mx-auto px-4">
          <p>© {new Date().getFullYear()} Learning App. All rights reserved.</p>
          <div className="mt-4 flex justify-center gap-4">
            <a href="#" className="hover:text-blue-400 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-blue-400 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-blue-400 transition-colors">Contact Us</a>
          </div>
        </div>
      </footer>

      {/* CSS Animations */}
      <style jsx global>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.5; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        @keyframes starTwinkle {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.7; }
        }
        
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        
        @keyframes backgroundMove {
          0% { background-position: 0% 0%; }
          100% { background-position: 100% 100%; }
        }
        
        .animate-pulse {
          animation: pulse 3s infinite;
        }
        
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        
        .animate-bounce {
          animation: bounce 3s infinite;
        }
      `}</style>
    </div>
  );
}