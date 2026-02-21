import React, { memo, useEffect, useState } from 'react';
import { Menu, X, Maximize2, Minimize2 } from 'lucide-react';

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  header?: React.ReactNode;
  className?: string;
}

// Breakpoint configuration
const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536
} as const;

// Memoized breakpoint hook
const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<keyof typeof BREAKPOINTS>('LG');
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      
      if (width < BREAKPOINTS.SM) {
        setBreakpoint('SM');
        setIsMobile(true);
      } else if (width < BREAKPOINTS.MD) {
        setBreakpoint('MD');
        setIsMobile(true);
      } else if (width < BREAKPOINTS.LG) {
        setBreakpoint('LG');
        setIsMobile(false);
      } else if (width < BREAKPOINTS.XL) {
        setBreakpoint('XL');
        setIsMobile(false);
      } else {
        setBreakpoint('2XL');
        setIsMobile(false);
      }
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);
    
    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  return { breakpoint, isMobile };
};

// Memoized sidebar component
const ResponsiveSidebar = memo(({ 
  children, 
  isOpen, 
  onToggle 
}: { 
  children: React.ReactNode; 
  isOpen: boolean; 
  onToggle: () => void; 
}) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
          aria-hidden="true"
        />
      )}
      
      {/* Sidebar */}
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50
        w-64 bg-[#111827] border-r border-[#1F2937]
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="h-full overflow-y-auto">
          {/* Mobile close button */}
          <button
            onClick={onToggle}
            className="absolute top-4 right-4 p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
          
          {/* Sidebar content */}
          <div className="p-4 pt-16 lg:pt-4">
            {children}
          </div>
        </div>
      </aside>
    </>
  );
});

ResponsiveSidebar.displayName = 'ResponsiveSidebar';

// Memoized header component
const ResponsiveHeader = memo(({ 
  children, 
  onSidebarToggle 
}: { 
  children: React.ReactNode; 
  onSidebarToggle: () => void; 
}) => {
  return (
    <header className="bg-[#111827] border-b border-[#1F2937] px-4 py-3 flex items-center justify-between">
      {/* Mobile menu button */}
      <button
        onClick={onSidebarToggle}
        className="p-2 rounded-lg bg-gray-800 text-gray-400 hover:text-white lg:hidden"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>
      
      {/* Header content */}
      <div className="flex-1 flex items-center justify-between">
        {children}
      </div>
    </header>
  );
});

ResponsiveHeader.displayName = 'ResponsiveHeader';

// Main responsive layout component
const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = memo(({ 
  children, 
  sidebar, 
  header, 
  className = '' 
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { isMobile } = useBreakpoint();

  // Close sidebar on mobile when route changes
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile]);

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#0B0F14] text-gray-200 ${className}`}>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        {sidebar && (
          <ResponsiveSidebar 
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebar}
          </ResponsiveSidebar>
        )}

        {/* Main content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          {header && (
            <ResponsiveHeader 
              onSidebarToggle={() => setSidebarOpen(!sidebarOpen)}
            >
              {header}
            </ResponsiveHeader>
          )}

          {/* Main content */}
          <main className="flex-1 overflow-auto">
            {/* Fullscreen toggle */}
            <button
              onClick={toggleFullscreen}
              className="fixed top-4 right-4 z-30 p-2 rounded-lg bg-gray-800/90 text-gray-400 hover:text-white backdrop-blur-sm border border-gray-700"
              aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            {/* Content */}
            <div className="p-4 lg:p-6 xl:p-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
});

ResponsiveLayout.displayName = 'ResponsiveLayout';

export default ResponsiveLayout;
export { useBreakpoint, BREAKPOINTS };
