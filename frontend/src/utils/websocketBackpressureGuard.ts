/**
 * WebSocket Backpressure Guard
 * Prevents message queue buildup and drops stale messages
 * Optimized for Intel i5 CPU, 8GB RAM
 */

export interface BackpressureConfig {
  maxQueueSize: number;
  maxAgeMs: number;
  dropStrategy: 'oldest' | 'newest';
  enableStats: boolean;
}

export interface QueuedMessage {
  id: string;
  data: any;
  timestamp: number;
  processed: boolean;
}

export interface BackpressureStats {
  totalReceived: number;
  totalProcessed: number;
  totalDropped: number;
  currentQueueSize: number;
  averageProcessingTime: number;
  lastDropTime: number | null;
}

export class WebSocketBackpressureGuard {
  private config: BackpressureConfig;
  private messageQueue: QueuedMessage[] = [];
  private isProcessing: boolean = false;
  private stats: BackpressureStats;
  private processingTimes: number[] = [];
  private messageIdCounter: number = 0;

  constructor(config: Partial<BackpressureConfig> = {}) {
    this.config = {
      maxQueueSize: 100,
      maxAgeMs: 1000, // 1 second max age
      dropStrategy: 'oldest',
      enableStats: true,
      ...config
    };

    this.stats = {
      totalReceived: 0,
      totalProcessed: 0,
      totalDropped: 0,
      currentQueueSize: 0,
      averageProcessingTime: 0,
      lastDropTime: null
    };

    // Start cleanup interval
    setInterval(() => this.cleanupStaleMessages(), this.config.maxAgeMs / 2);
  }

  /**
   * Add a message to the queue with backpressure handling
   */
  public addMessage(data: any): boolean {
    const messageId = `msg_${++this.messageIdCounter}`;
    const timestamp = Date.now();

    this.stats.totalReceived++;

    // Check if we should drop this message
    if (this.shouldDropMessage(timestamp)) {
      this.stats.totalDropped++;
      this.stats.lastDropTime = timestamp;
      
      if (this.config.enableStats) {
        console.warn(`WebSocket backpressure: dropping message ${messageId}`);
      }
      
      return false;
    }

    // Add to queue
    const queuedMessage: QueuedMessage = {
      id: messageId,
      data,
      timestamp,
      processed: false
    };

    this.messageQueue.push(queuedMessage);
    this.stats.currentQueueSize = this.messageQueue.length;

    // Start processing if not already running
    if (!this.isProcessing) {
      this.processQueue();
    }

    return true;
  }

  /**
   * Get the latest message (drop all others)
   */
  public getLatestMessage(): any | null {
    if (this.messageQueue.length === 0) {
      return null;
    }

    // Get the newest message
    const latestMessage = this.messageQueue[this.messageQueue.length - 1];
    
    // Clear queue except latest
    this.messageQueue = [latestMessage];
    this.stats.currentQueueSize = 1;

    return latestMessage.data;
  }

  /**
   * Process all queued messages
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.messageQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      while (this.messageQueue.length > 0) {
        const message = this.messageQueue[0];
        const startTime = Date.now();

        // Process the message (this would be handled by the actual WebSocket handler)
        await this.processMessage(message);

        // Update stats
        const processingTime = Date.now() - startTime;
        this.processingTimes.push(processingTime);
        
        // Keep only last 100 processing times for average
        if (this.processingTimes.length > 100) {
          this.processingTimes.shift();
        }

        this.stats.totalProcessed++;
        this.stats.currentQueueSize = this.messageQueue.length;

        // Remove processed message
        this.messageQueue.shift();
      }
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Process a single message (to be overridden by actual implementation)
   */
  private async processMessage(message: QueuedMessage): Promise<void> {
    // This would be replaced with actual message processing logic
    // For now, just mark as processed
    message.processed = true;
  }

  /**
   * Check if a message should be dropped due to backpressure
   */
  private shouldDropMessage(timestamp: number): boolean {
    // Check queue size
    if (this.messageQueue.length >= this.config.maxQueueSize) {
      return true;
    }

    // Check message age
    const oldestMessage = this.messageQueue[0];
    if (oldestMessage && timestamp - oldestMessage.timestamp > this.config.maxAgeMs) {
      return true;
    }

    return false;
  }

  /**
   * Clean up stale messages
   */
  private cleanupStaleMessages(): void {
    const now = Date.now();
    const initialLength = this.messageQueue.length;

    // Remove stale messages
    this.messageQueue = this.messageQueue.filter(
      message => now - message.timestamp <= this.config.maxAgeMs
    );

    const droppedCount = initialLength - this.messageQueue.length;
    if (droppedCount > 0) {
      this.stats.totalDropped += droppedCount;
      this.stats.currentQueueSize = this.messageQueue.length;
      
      if (this.config.enableStats) {
        console.warn(`WebSocket backpressure: cleaned up ${droppedCount} stale messages`);
      }
    }
  }

  /**
   * Get current statistics
   */
  public getStats(): BackpressureStats {
    // Calculate average processing time
    if (this.processingTimes.length > 0) {
      this.stats.averageProcessingTime = 
        this.processingTimes.reduce((sum, time) => sum + time, 0) / this.processingTimes.length;
    }

    return { ...this.stats };
  }

  /**
   * Reset statistics
   */
  public resetStats(): void {
    this.stats = {
      totalReceived: 0,
      totalProcessed: 0,
      totalDropped: 0,
      currentQueueSize: this.messageQueue.length,
      averageProcessingTime: 0,
      lastDropTime: null
    };
    this.processingTimes = [];
  }

  /**
   * Get current queue size
   */
  public getQueueSize(): number {
    return this.messageQueue.length;
  }

  /**
   * Check if the guard is currently processing
   */
  public isProcessingQueue(): boolean {
    return this.isProcessing;
  }

  /**
   * Clear all queued messages
   */
  public clearQueue(): void {
    const droppedCount = this.messageQueue.length;
    this.messageQueue = [];
    this.stats.currentQueueSize = 0;
    this.stats.totalDropped += droppedCount;
    
    if (this.config.enableStats) {
      console.warn(`WebSocket backpressure: cleared ${droppedCount} messages`);
    }
  }

  /**
   * Update configuration
   */
  public updateConfig(newConfig: Partial<BackpressureConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  public getConfig(): BackpressureConfig {
    return { ...this.config };
  }
}

// Default instance for immediate use
export const defaultBackpressureGuard = new WebSocketBackpressureGuard({
  maxQueueSize: 50,
  maxAgeMs: 500,
  dropStrategy: 'oldest',
  enableStats: process.env.NODE_ENV === 'development'
});

// Utility functions for common use cases
export const createStrictGuard = () => new WebSocketBackpressureGuard({
  maxQueueSize: 10,
  maxAgeMs: 200,
  dropStrategy: 'oldest',
  enableStats: true
});

export const createLenientGuard = () => new WebSocketBackpressureGuard({
  maxQueueSize: 200,
  maxAgeMs: 2000,
  dropStrategy: 'newest',
  enableStats: false
});

// React hook for using the guard
export const useWebSocketBackpressure = (config?: Partial<BackpressureConfig>) => {
  const guard = React.useMemo(() => 
    new WebSocketBackpressureGuard(config), 
    [config]
  );

  React.useEffect(() => {
    return () => {
      guard.clearQueue();
    };
  }, [guard]);

  return guard;
};
