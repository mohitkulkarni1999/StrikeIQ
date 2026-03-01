/**
 * MARKET STATUS VALIDATION CHAOS TEST
 * Test market status accuracy at critical times
 */

const { JSDOM } = require('jsdom');

// Mock market status utility
class MarketStatusManager {
  constructor() {
    this.MARKET_OPEN_TIME = { hour: 9, minute: 15 }; // 09:15 IST
    this.MARKET_CLOSE_TIME = { hour: 15, minute: 30 }; // 15:30 IST
    this.TRADING_DAYS = [1, 2, 3, 4, 5]; // Monday - Friday (1-5)
    this.IST_OFFSET = 5.5 * 60 * 60 * 1000; // IST is UTC+5:30
  }

  // Get current time in IST (allows for custom time injection)
  getCurrentISTTime(customTime = null) {
    if (customTime) {
      return customTime;
    }
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    return new Date(utcTime + this.IST_OFFSET);
  }

  getMarketStatus(customTime = null) {
    const nowIST = this.getCurrentISTTime(customTime);
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

  getNextOpenTime(currentTime) {
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

  getDayName(dayOfWeek) {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    return days[dayOfWeek];
  }

  getFormattedStatus(customTime = null) {
    const status = this.getMarketStatus(customTime);
    
    let timeUntil;
    
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

  getStatusText(status) {
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

  getStatusColor(status) {
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

  getTimeUntilEvent(targetTime) {
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
}

class MarketStatusChaosTester {
  constructor() {
    this.testResults = {};
    this.marketStatus = new MarketStatusManager();
  }

  async runAllTests() {
    console.log('🕐 STARTING MARKET STATUS VALIDATION CHAOS TESTS');
    console.log('='.repeat(55));
    
    try {
      await this.test_0914_IST_market_closed();
      await this.test_0915_ist_market_open();
      await this.test_1530_ist_market_closed();
      await this.test_weekend_market_closed();
      await this.test_holiday_market_closed();
      await this.test_pre_market_status();
      await this.test_post_market_status();
      await this.test_timezone_accuracy();
      
      return this.generateReport();
    } catch (error) {
      console.error('❌ Market status chaos test failed:', error);
      throw error;
    }
  }

  async test_0914_ist_market_closed() {
    console.log('\n🕘 Testing 09:14 IST → MARKET CLOSED...');
    
    try {
      // Create custom time for 09:14 IST on a weekday
      const testDate = new Date('2026-03-01T09:14:00+05:30'); // Monday 09:14 IST
      
      const status = this.marketStatus.getMarketStatus(testDate);
      const formattedStatus = this.marketStatus.getFormattedStatus(testDate);
      
      // Verify market is closed at 09:14
      const isCorrect = !status.isOpen && status.status === 'PRE_MARKET';
      const textCorrect = formattedStatus.text === 'PRE-MARKET';
      const colorCorrect = formattedStatus.color === '#f59e0b'; // amber-500
      
      this.testResults['0914_ist_market_closed'] = {
        status: isCorrect && textCorrect && colorCorrect ? 'PASS' : 'FAIL',
        message: `09:14 IST status: ${status.status}`,
        testTime: '09:14 IST',
        expectedStatus: 'PRE_MARKET',
        actualStatus: status.status,
        isOpen: status.isOpen,
        statusText: formattedStatus.text,
        statusColor: formattedStatus.color,
        textCorrect: textCorrect,
        colorCorrect: colorCorrect,
        overallCorrect: isCorrect && textCorrect && colorCorrect
      };
      
    } catch (error) {
      this.testResults['0914_ist_market_closed'] = {
        status: 'FAIL',
        message: `09:14 IST test failed: ${error.message}`
      };
    }
  }

  async test_0915_ist_market_open() {
    console.log('\n🕘 Testing 09:15 IST → MARKET OPEN...');
    
    try {
      // Create custom time for 09:15 IST on a weekday
      const testDate = new Date('2026-03-01T09:15:00+05:30'); // Monday 09:15 IST
      
      const status = this.marketStatus.getMarketStatus(testDate);
      const formattedStatus = this.marketStatus.getFormattedStatus(testDate);
      
      // Verify market is open at 09:15
      const isCorrect = status.isOpen && status.status === 'OPEN';
      const textCorrect = formattedStatus.text === 'MARKET OPEN';
      const colorCorrect = formattedStatus.color === '#10b981'; // green-500
      
      this.testResults['0915_ist_market_open'] = {
        status: isCorrect && textCorrect && colorCorrect ? 'PASS' : 'FAIL',
        message: `09:15 IST status: ${status.status}`,
        testTime: '09:15 IST',
        expectedStatus: 'OPEN',
        actualStatus: status.status,
        isOpen: status.isOpen,
        statusText: formattedStatus.text,
        statusColor: formattedStatus.color,
        textCorrect: textCorrect,
        colorCorrect: colorCorrect,
        overallCorrect: isCorrect && textCorrect && colorCorrect
      };
      
    } catch (error) {
      this.testResults['0915_ist_market_open'] = {
        status: 'FAIL',
        message: `09:15 IST test failed: ${error.message}`
      };
    }
  }

  async test_1530_ist_market_closed() {
    console.log('\n🕒 Testing 15:30 IST → MARKET CLOSED...');
    
    try {
      // Create custom time for 15:30 IST on a weekday
      const testDate = new Date('2026-03-01T15:30:00+05:30'); // Monday 15:30 IST
      
      const status = this.marketStatus.getMarketStatus(testDate);
      const formattedStatus = this.marketStatus.getFormattedStatus(testDate);
      
      // Verify market is closed at 15:30
      const isCorrect = !status.isOpen && status.status === 'POST_MARKET';
      const textCorrect = formattedStatus.text === 'POST-MARKET';
      const colorCorrect = formattedStatus.color === '#6b7280'; // gray-500
      
      this.testResults['1530_ist_market_closed'] = {
        status: isCorrect && textCorrect && colorCorrect ? 'PASS' : 'FAIL',
        message: `15:30 IST status: ${status.status}`,
        testTime: '15:30 IST',
        expectedStatus: 'POST_MARKET',
        actualStatus: status.status,
        isOpen: status.isOpen,
        statusText: formattedStatus.text,
        statusColor: formattedStatus.color,
        textCorrect: textCorrect,
        colorCorrect: colorCorrect,
        overallCorrect: isCorrect && textCorrect && colorCorrect
      };
      
    } catch (error) {
      this.testResults['1530_ist_market_closed'] = {
        status: 'FAIL',
        message: `15:30 IST test failed: ${error.message}`
      };
    }
  }

  async test_weekend_market_closed() {
    console.log('\n📅 Testing Weekend Market Closed...');
    
    try {
      // Test Saturday
      const saturdayDate = new Date('2026-03-07T10:00:00+05:30'); // Saturday 10:00 IST
      const saturdayStatus = this.marketStatus.getMarketStatus(saturdayDate);
      
      // Test Sunday  
      const sundayDate = new Date('2026-03-08T10:00:00+05:30'); // Sunday 10:00 IST
      const sundayStatus = this.marketStatus.getMarketStatus(sundayDate);
      
      const saturdayCorrect = !saturdayStatus.isOpen && saturdayStatus.status === 'CLOSED';
      const sundayCorrect = !sundayStatus.isOpen && sundayStatus.status === 'CLOSED';
      
      this.testResults['weekend_market_closed'] = {
        status: saturdayCorrect && sundayCorrect ? 'PASS' : 'FAIL',
        message: `Weekend market status test`,
        saturday: {
          day: 'Saturday',
          isOpen: saturdayStatus.isOpen,
          status: saturdayStatus.status,
          correct: saturdayCorrect
        },
        sunday: {
          day: 'Sunday', 
          isOpen: sundayStatus.isOpen,
          status: sundayStatus.status,
          correct: sundayCorrect
        },
        overallCorrect: saturdayCorrect && sundayCorrect
      };
      
    } catch (error) {
      this.testResults['weekend_market_closed'] = {
        status: 'FAIL',
        message: `Weekend test failed: ${error.message}`
      };
    }
  }

  async test_holiday_market_closed() {
    console.log('\n🎉 Testing Holiday Market Closed...');
    
    try {
      // Test on a holiday (e.g., Diwali - this would need actual holiday calendar)
      // For this test, we'll simulate a holiday on a weekday
      const holidayDate = new Date('2026-10-31T10:00:00+05:30'); // Weekend day for simulation
      
      // In a real implementation, this would check against a holiday calendar
      // For now, we'll test that weekends are correctly identified as closed
      const status = this.marketStatus.getMarketStatus(holidayDate);
      
      const isWeekend = [0, 6].includes(holidayDate.getDay()); // Sunday or Saturday
      const correctStatus = isWeekend && !status.isOpen && status.status === 'CLOSED';
      
      this.testResults['holiday_market_closed'] = {
        status: correctStatus ? 'PASS' : 'PARTIAL',
        message: `Holiday market status test (simulated)`,
        testDate: holidayDate.toISOString(),
        dayOfWeek: holidayDate.getDay(),
        isWeekend: isWeekend,
        isOpen: status.isOpen,
        status: status.status,
        correctStatus: correctStatus,
        note: 'Holiday calendar integration needed for full implementation'
      };
      
    } catch (error) {
      this.testResults['holiday_market_closed'] = {
        status: 'FAIL',
        message: `Holiday test failed: ${error.message}`
      };
    }
  }

  async test_pre_market_status() {
    console.log('\n🌅 Testing Pre-Market Status...');
    
    try {
      // Test various pre-market times
      const preMarketTests = [
        { time: '08:00', expected: 'PRE_MARKET' },
        { time: '08:30', expected: 'PRE_MARKET' },
        { time: '09:00', expected: 'PRE_MARKET' },
        { time: '09:14', expected: 'PRE_MARKET' }
      ];
      
      const results = [];
      
      for (const test of preMarketTests) {
        const testDate = new Date(`2026-03-01T${test.time}:00+05:30`);
        const status = this.marketStatus.getMarketStatus(testDate);
        const correct = status.status === test.expected;
        
        results.push({
          time: test.time,
          expected: test.expected,
          actual: status.status,
          correct: correct,
          isOpen: status.isOpen
        });
      }
      
      const allCorrect = results.every(r => r.correct);
      
      this.testResults['pre_market_status'] = {
        status: allCorrect ? 'PASS' : 'FAIL',
        message: `Pre-market status test`,
        tests: results,
        allCorrect: allCorrect,
        correctCount: results.filter(r => r.correct).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults['pre_market_status'] = {
        status: 'FAIL',
        message: `Pre-market test failed: ${error.message}`
      };
    }
  }

  async test_post_market_status() {
    console.log('\n🌆 Testing Post-Market Status...');
    
    try {
      // Test various post-market times
      const postMarketTests = [
        { time: '15:31', expected: 'POST_MARKET' },
        { time: '16:00', expected: 'POST_MARKET' },
        { time: '18:00', expected: 'POST_MARKET' },
        { time: '20:00', expected: 'POST_MARKET' }
      ];
      
      const results = [];
      
      for (const test of postMarketTests) {
        const testDate = new Date(`2026-03-01T${test.time}:00+05:30`);
        const status = this.marketStatus.getMarketStatus(testDate);
        const correct = status.status === test.expected;
        
        results.push({
          time: test.time,
          expected: test.expected,
          actual: status.status,
          correct: correct,
          isOpen: status.isOpen
        });
      }
      
      const allCorrect = results.every(r => r.correct);
      
      this.testResults['post_market_status'] = {
        status: allCorrect ? 'PASS' : 'FAIL',
        message: `Post-market status test`,
        tests: results,
        allCorrect: allCorrect,
        correctCount: results.filter(r => r.correct).length,
        totalCount: results.length
      };
      
    } catch (error) {
      this.testResults['post_market_status'] = {
        status: 'FAIL',
        message: `Post-market test failed: ${error.message}`
      };
    }
  }

  async test_timezone_accuracy() {
    console.log('\n🌍 Testing Timezone Accuracy...');
    
    try {
      // Test timezone conversion accuracy
      const utcTime = new Date('2026-03-01T03:45:00Z'); // 03:45 UTC
      const istTime = new Date('2026-03-01T09:15:00+05:30'); // 09:15 IST
      
      // Test that the utility correctly converts to IST
      const convertedTime = this.marketStatus.getCurrentISTTime(utcTime);
      const status = this.marketStatus.getMarketStatus(convertedTime);
      
      // Should be market open at 09:15 IST
      const correct = status.isOpen && status.status === 'OPEN';
      
      this.testResults['timezone_accuracy'] = {
        status: correct ? 'PASS' : 'FAIL',
        message: `Timezone accuracy test`,
        utcTime: utcTime.toISOString(),
        expectedIST: istTime.toISOString(),
        convertedTime: convertedTime.toISOString(),
        marketStatus: status.status,
        isOpen: status.isOpen,
        correct: correct
      };
      
    } catch (error) {
      this.testResults['timezone_accuracy'] = {
        status: 'FAIL',
        message: `Timezone test failed: ${error.message}`
      };
    }
  }

  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      testType: 'MARKET_STATUS_VALIDATION_CHAOS_TEST',
      summary: {
        totalTests: Object.keys(this.testResults).length,
        passed: Object.values(this.testResults).filter(r => r.status === 'PASS').length,
        failed: Object.values(this.testResults).filter(r => r.status === 'FAIL').length,
        partial: Object.values(this.testResults).filter(r => r.status === 'PARTIAL').length,
      },
      results: this.testResults,
      marketHours: {
        open: '09:15 IST',
        close: '15:30 IST',
        tradingDays: 'Monday - Friday'
      }
    };

    return report;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const tester = new MarketStatusChaosTester();
  
  tester.runAllTests()
    .then(report => {
      console.log('\n🕐 MARKET STATUS VALIDATION CHAOS TEST REPORT');
      console.log('='.repeat(50));
      console.log(`Total Tests: ${report.summary.totalTests}`);
      console.log(`Passed: ${report.summary.passed}`);
      console.log(`Failed: ${report.summary.failed}`);
      console.log(`Partial: ${report.summary.partial}`);
      
      console.log('\nDetailed Results:');
      Object.entries(report.results).forEach(([test, result]) => {
        const icon = result.status === 'PASS' ? '✅' : 
                    result.status === 'FAIL' ? '❌' : '⚠️';
        console.log(`${icon} ${test}: ${result.message}`);
      });
      
      console.log('\nMarket Hours Configuration:');
      console.log(`Open: ${report.marketHours.open}`);
      console.log(`Close: ${report.marketHours.close}`);
      console.log(`Trading Days: ${report.marketHours.tradingDays}`);
      
      // Save report to file
      require('fs').writeFileSync(
        'market_status_chaos_test_report.json',
        JSON.stringify(report, null, 2)
      );
      console.log('\n📄 Report saved to market_status_chaos_test_report.json');
    })
    .catch(error => {
      console.error('❌ Market status chaos test execution failed:', error);
      process.exit(1);
    });
}

module.exports = MarketStatusChaosTester;
