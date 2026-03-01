/**
 * MARKET STATUS UTILITY
 * 
 * Automatically detects market status based on trading hours:
 * - Trading hours: 09:15 – 15:30 IST
 * - Trading days: Monday – Friday
 * 
 * Displays:
 * - MARKET OPEN (green indicator)
 * - MARKET CLOSED (red indicator)
 */

export interface MarketStatus {
  isOpen: boolean;
  status: 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'POST_MARKET';
  nextOpenTime: Date | null;
  nextCloseTime: Date | null;
  currentTime: Date;
  dayOfWeek: string;
}

class MarketStatusManager {
  private readonly MARKET_OPEN_TIME = { hour: 9, minute: 15 }; // 09:15 IST
  private readonly MARKET_CLOSE_TIME = { hour: 15, minute: 30 }; // 15:30 IST
  private readonly TRADING_DAYS = [1, 2, 3, 4, 5]; // Monday - Friday (1-5)
  private readonly IST_OFFSET = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30

  /**
   * Get current market status
   */
  getMarketStatus(): MarketStatus {
    const nowIST = this.getCurrentISTTime();
    const dayOfWeek = nowIST.getDay();
    const currentTime = nowIST.getTime();
    
    // Check if it's a trading day
    const isTradingDay = this.TRADING_DAYS.includes(dayOfWeek);
    
    if (!isTradingDay) {
      return {
        isOpen: false,
        status: 'CLOSED',
        nextOpenTime: this.getNextOpenTime(nowIST),
        nextCloseTime: null,
        currentTime: nowIST,
        dayOfWeek: this.getDayName(dayOfWeek),
      };
    }

    // Get market open and close times for today
    const marketOpenTime = new Date(nowIST);
    marketOpenTime.setHours(this.MARKET_OPEN_TIME.hour, this.MARKET_OPEN_TIME.minute, 0, 0);
    
    const marketCloseTime = new Date(nowIST);
    marketCloseTime.setHours(this.MARKET_CLOSE_TIME.hour, this.MARKET_CLOSE_TIME.minute, 0, 0);

    // Determine market status
    if (currentTime >= marketOpenTime.getTime() && currentTime <= marketCloseTime.getTime()) {
      return {
        isOpen: true,
        status: 'OPEN',
        nextOpenTime: null,
        nextCloseTime: marketCloseTime,
        currentTime: nowIST,
        dayOfWeek: this.getDayName(dayOfWeek),
      };
    } else if (currentTime < marketOpenTime.getTime()) {
      return {
        isOpen: false,
        status: 'PRE_MARKET',
        nextOpenTime: marketOpenTime,
        nextCloseTime: marketCloseTime,
        currentTime: nowIST,
        dayOfWeek: this.getDayName(dayOfWeek),
      };
    } else {
      return {
        isOpen: false,
        status: 'POST_MARKET',
        nextOpenTime: this.getNextOpenTime(nowIST),
        nextCloseTime: null,
        currentTime: nowIST,
        dayOfWeek: this.getDayName(dayOfWeek),
      };
    }
  }

  /**
   * Get current time in IST
   */
  private getCurrentISTTime(): Date {
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    return new Date(utcTime + this.IST_OFFSET);
  }

  /**
   * Get next market open time
   */
  private getNextOpenTime(currentTime: Date): Date {
    let nextOpen = new Date(currentTime);
    let dayOfWeek = nextOpen.getDay();
    
    // Move to next trading day
    do {
      nextOpen.setDate(nextOpen.getDate() + 1);
      dayOfWeek = nextOpen.getDay();
    } while (!this.TRADING_DAYS.includes(dayOfWeek));
    
    // Set market open time
    nextOpen.setHours(this.MARKET_OPEN_TIME.hour, this.MARKET_OPEN_TIME.minute, 0, 0);
    
    return nextOpen;
  }

  /**
   * Get day name
   */
  private getDayName(dayOfWeek: number): string {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[dayOfWeek];
  }

  /**
   * Format time until market opens/closes
   */
  getTimeUntilEvent(targetTime: Date): string {
    const now = this.getCurrentISTTime();
    const diff = targetTime.getTime() - now.getTime();
    
    if (diff <= 0) {
      return 'Now';
    }
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  /**
   * Get market status color
   */
  getStatusColor(status: MarketStatus['status']): string {
    switch (status) {
      case 'OPEN':
        return '#10b981'; // green-500
      case 'CLOSED':
        return '#ef4444'; // red-500
      case 'PRE_MARKET':
        return '#f59e0b'; // amber-500
      case 'POST_MARKET':
        return '#6b7280'; // gray-500
      default:
        return '#6b7280'; // gray-500
    }
  }

  /**
   * Get market status text
   */
  getStatusText(status: MarketStatus['status']): string {
    switch (status) {
      case 'OPEN':
        return 'MARKET OPEN';
      case 'CLOSED':
        return 'MARKET CLOSED';
      case 'PRE_MARKET':
        return 'PRE-MARKET';
      case 'POST_MARKET':
        return 'POST-MARKET';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Check if market is within trading hours
   */
  isWithinTradingHours(): boolean {
    const status = this.getMarketStatus();
    return status.isOpen;
  }

  /**
   * Get formatted market status for display
   */
  getFormattedStatus(): {
    text: string;
    color: string;
    isOpen: boolean;
    timeUntil?: string;
    dayOfWeek: string;
    currentTime: string;
  } {
    const status = this.getMarketStatus();
    
    let timeUntil: string | undefined;
    
    if (status.nextOpenTime && !status.isOpen) {
      timeUntil = `Opens in ${this.getTimeUntilEvent(status.nextOpenTime)}`;
    } else if (status.nextCloseTime && status.isOpen) {
      timeUntil = `Closes in ${this.getTimeUntilEvent(status.nextCloseTime)}`;
    }
    
    return {
      text: this.getStatusText(status.status),
      color: this.getStatusColor(status.status),
      isOpen: status.isOpen,
      timeUntil,
      dayOfWeek: status.dayOfWeek,
      currentTime: status.currentTime.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata'
      }),
    };
  }
}

// Create singleton instance
const marketStatusManager = new MarketStatusManager();

export default marketStatusManager;
export { MarketStatusManager };
