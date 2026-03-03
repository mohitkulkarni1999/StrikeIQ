/**
 * Frontend Logger for StrikeIQ Realtime Trading System
 * Structured logging with service prefixes and trace tracking
 */

export interface LogContext {
  traceId?: string;
  component?: string;
  [key: string]: any;
}

class Logger {
  private static instance: Logger;
  private currentTraceId: string | null = null;

  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  startTrace(): string {
    this.currentTraceId = Math.random().toString(36).substring(2, 10).toUpperCase();
    return this.currentTraceId;
  }

  getTraceId(): string {
    return this.currentTraceId || 'NO_TRACE';
  }

  clearTrace(): void {
    this.currentTraceId = null;
  }

  private formatMessage(level: string, service: string, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const traceId = context?.traceId || this.getTraceId();
    const tracePrefix = traceId !== 'NO_TRACE' ? `[TRACE ${traceId}] ` : '';
    
    // Format context as key=value pairs
    const contextStr = context ? 
      Object.entries(context)
        .filter(([key]) => key !== 'traceId')
        .map(([key, value]) => `${key}=${value}`)
        .join(' ') : '';
    
    const contextSuffix = contextStr ? ` ${contextStr}` : '';
    
    return `[${timestamp}] [${level}] [${service}] ${tracePrefix}${message}${contextSuffix}`;
  }

  debug(service: string, message: string, context?: LogContext): void {
    console.debug(this.formatMessage('DEBUG', service, message, context));
  }

  info(service: string, message: string, context?: LogContext): void {
    console.info(this.formatMessage('INFO', service, message, context));
  }

  warn(service: string, message: string, context?: LogContext): void {
    console.warn(this.formatMessage('WARN', service, message, context));
  }

  error(service: string, message: string, context?: LogContext): void {
    console.error(this.formatMessage('ERROR', service, message, context));
  }
}

// Global logger instance
const logger = Logger.getInstance();

// Service-specific loggers
export const wsLogger = {
  debug: (message: string, context?: LogContext) => logger.debug('WS', message, context),
  info: (message: string, context?: LogContext) => logger.info('WS', message, context),
  warn: (message: string, context?: LogContext) => logger.warn('WS', message, context),
  error: (message: string, context?: LogContext) => logger.error('WS', message, context),
};

export const storeLogger = {
  debug: (message: string, context?: LogContext) => logger.debug('STORE', message, context),
  info: (message: string, context?: LogContext) => logger.info('STORE', message, context),
  warn: (message: string, context?: LogContext) => logger.warn('STORE', message, context),
  error: (message: string, context?: LogContext) => logger.error('STORE', message, context),
};

export const apiLogger = {
  debug: (message: string, context?: LogContext) => logger.debug('API', message, context),
  info: (message: string, context?: LogContext) => logger.info('API', message, context),
  warn: (message: string, context?: LogContext) => logger.warn('API', message, context),
  error: (message: string, context?: LogContext) => logger.error('API', message, context),
};

export const uiLogger = {
  debug: (message: string, context?: LogContext) => logger.debug('UI', message, context),
  info: (message: string, context?: LogContext) => logger.info('UI', message, context),
  warn: (message: string, context?: LogContext) => logger.warn('UI', message, context),
  error: (message: string, context?: LogContext) => logger.error('UI', message, context),
};

// Trace management
export const traceManager = {
  startTrace: () => logger.startTrace(),
  getTraceId: () => logger.getTraceId(),
  clearTrace: () => logger.clearTrace(),
};

// Higher-order function for automatic trace management
export function withTrace<T extends any[], R>(
  fn: (...args: T) => R,
  serviceName?: string
): (...args: T) => R {
  return (...args: T): R => {
    const traceId = logger.startTrace();
    
    if (serviceName) {
      logger.info(serviceName, 'TRACE STARTED', { traceId });
    }
    
    try {
      const result = fn(...args);
      
      if (serviceName) {
        logger.info(serviceName, 'TRACE COMPLETED', { traceId });
      }
      
      return result;
    } catch (error) {
      if (serviceName) {
        logger.error(serviceName, 'TRACE ERROR', { traceId, error: String(error) });
      }
      throw error;
    } finally {
      logger.clearTrace();
    }
  };
}

export default logger;
