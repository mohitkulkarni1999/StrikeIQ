import React from 'react';
import { Terminal, Loader2 } from 'lucide-react';

export default function TerminalLoadingState() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="flex items-center justify-center mb-6">
          <Terminal className="w-8 h-8 text-primary-400 mr-3" />
          <Loader2 className="w-6 h-6 text-primary-400 animate-spin" />
        </div>
        <div className="text-white text-lg font-medium mb-2">Initializing Terminal</div>
        <div className="text-muted-foreground text-sm">Establishing secure connection...</div>
      </div>
    </div>
  );
}
