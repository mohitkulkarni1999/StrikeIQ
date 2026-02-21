# Spring Boot Migration Plan - Smart Money Engine

## 📋 Python Module Analysis

### **Source File**: `app/services/market_data/smart_money_engine.py`

#### **Business Logic Identified**
1. **Smart Money Signal Generation** - Analyzes option chain data to detect institutional activity
2. **PCR (Put-Call Ratio) Calculation** - Measures market sentiment
3. **OI Acceleration Detection** - Identifies unusual Open Interest changes
4. **ATM Straddle Analysis** - Calculates expected move from ATM options
5. **IV Regime Classification** - Categorizes volatility levels
6. **Bias Generation** - Produces BULLISH/BEARISH/NEUTRAL signals
7. **Confidence Scoring** - Calculates signal reliability (0-100)
8. **Caching Layer** - 30-second TTL for performance

#### **Data Processing Flow**
```
OptionChainSnapshots (DB) 
    → Feature Calculation (PCR, OI, IV, Straddle)
    → Time-based Analysis (15-min averages, shifts)
    → Signal Generation (Bias + Confidence)
    → Response Formatting
    → Cache Storage
```

#### **Database Interactions**
- **Query**: Latest 30 snapshots per symbol
- **Filter**: By symbol and timestamp range
- **Aggregate**: Total OI, PCR calculations
- **Performance**: Optimized queries with indexes

#### **Validation Logic**
- Symbol validation: NIFTY, BANKNIFTY only
- Data sufficiency checks
- Cache TTL validation
- Error handling with fallback responses

#### **External API Usage**
- None (pure analytics engine)
- Uses cached market data from database

#### **Transactional Operations**
- Read-only operations
- No database writes
- Cache updates (in-memory)

---

## 🏗️ Spring Boot Layered Architecture Mapping

### **1. Package Structure**
```
com.strikeiq.analytics/
├── controller/
│   └── SmartMoneyController.java
├── service/
│   ├── SmartMoneyService.java
│   └── SmartMoneyCalculationService.java
├── repository/
│   ├── OptionChainSnapshotRepository.java
│   └── MarketSnapshotRepository.java
├── entity/
│   ├── OptionChainSnapshot.java
│   ├── MarketSnapshot.java
│   └── SmartMoneyPrediction.java
├── dto/
│   ├── SmartMoneySignalRequest.java
│   ├── SmartMoneySignalResponse.java
│   ├── SmartMoneyMetrics.java
│   └── BiasAnalysis.java
└── exception/
    ├── SmartMoneyException.java
    └── InsufficientDataException.java
```

### **2. Entity Class Design**

#### **OptionChainSnapshot.java**
```java
@Entity
@Table(name = "option_chain_snapshots")
@IdClass(OptionChainSnapshotId.class)
public class OptionChainSnapshot {
    
    @Id
    private Integer id;
    
    @Id
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "market_snapshot_id")
    private MarketSnapshot marketSnapshot;
    
    @Column(nullable = false, index = true)
    private String symbol;
    
    @Column(nullable = false)
    private LocalDateTime timestamp;
    
    @Column(nullable = false)
    private Double strike;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OptionType optionType; // CE, PE
    
    @Column(nullable = false)
    private String expiry;
    
    @Column(nullable = false)
    private Long openInterest;
    
    @Column(name = "oi_change")
    private Long openInterestChange;
    
    @Column(name = "prev_oi")
    private Long previousOpenInterest;
    
    @Column(name = "oi_delta")
    private Long openInterestDelta;
    
    @Column(nullable = false)
    private Double lastTradedPrice;
    
    @Column
    private Double impliedVolatility;
    
    @Column
    private Long volume;
    
    @Column
    private Double theta;
    
    @Column
    private Double delta;
    
    @Column
    private Double gamma;
    
    @Column
    private Double vega;
    
    // Constructors, getters, setters
}

public enum OptionType {
    CALL("CE"),
    PUT("PE");
    
    private final String code;
    OptionType(String code) { this.code = code; }
    public String getCode() { return code; }
}
```

#### **SmartMoneyPrediction.java**
```java
@Entity
@Table(name = "smart_money_predictions")
public class SmartMoneyPrediction {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(nullable = false, index = true)
    private LocalDateTime timestamp;
    
    @Column(nullable = false, index = true)
    private String symbol;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private MarketBias bias;
    
    @Column(nullable = false)
    private Double confidence;
    
    // Metrics at prediction time
    @Column(name = "pcr")
    private Double putCallRatio;
    
    @Column(name = "pcr_shift_z")
    private Double pcrShiftZ;
    
    @Column(name = "atm_straddle")
    private Double atmStraddle;
    
    @Column(name = "straddle_change_normalized")
    private Double straddleChangeNormalized;
    
    @Column(name = "oi_acceleration_ratio")
    private Double openInterestAccelerationRatio;
    
    @Enumerated(EnumType.STRING)
    private VolatilityRegime ivRegime;
    
    // Performance tracking
    @Column(name = "actual_move")
    private Double actualMove;
    
    @Enumerated(EnumType.STRING)
    private PredictionResult result;
    
    @Column(name = "model_version")
    private String modelVersion = "v1.0";
    
    @Column(name = "expiry_date")
    private String expiryDate;
    
    // Constructors, getters, setters
}

public enum MarketBias {
    BULLISH, BEARISH, NEUTRAL
}

public enum VolatilityRegime {
    LOW, NORMAL, HIGH
}

public enum PredictionResult {
    CORRECT, WRONG, NEUTRAL
}
```

### **3. Repository Interface**

#### **OptionChainSnapshotRepository.java**
```java
@Repository
public interface OptionChainSnapshotRepository extends JpaRepository<OptionChainSnapshot, OptionChainSnapshotId> {
    
    @Query("SELECT DISTINCT ocs.timestamp FROM OptionChainSnapshot ocs " +
            "WHERE ocs.symbol = :symbol " +
            "ORDER BY ocs.timestamp DESC")
    List<LocalDateTime> findLatestTimestamps(@Param("symbol") String symbol, Pageable pageable);
    
    @Query("SELECT ocs FROM OptionChainSnapshot ocs " +
            "WHERE ocs.symbol = :symbol " +
            "AND ocs.timestamp IN :timestamps " +
            "ORDER BY ocs.timestamp DESC")
    List<OptionChainSnapshot> findBySymbolAndTimestamps(
        @Param("symbol") String symbol,
        @Param("timestamps") List<LocalDateTime> timestamps
    );
    
    @Query("SELECT ocs FROM OptionChainSnapshot ocs " +
            "WHERE ocs.symbol = :symbol " +
            "AND ocs.timestamp >= :since " +
            "ORDER BY ocs.timestamp DESC")
    List<OptionChainSnapshot> findRecentSnapshots(
        @Param("symbol") String symbol,
        @Param("since") LocalDateTime since
    );
    
    // Find snapshots for specific strike range
    @Query("SELECT ocs FROM OptionChainSnapshot ocs " +
            "WHERE ocs.symbol = :symbol " +
            "AND ocs.strike BETWEEN :minStrike AND :maxStrike " +
            "AND ocs.timestamp = :timestamp")
    List<OptionChainSnapshot> findBySymbolStrikeRangeAndTimestamp(
        @Param("symbol") String symbol,
        @Param("minStrike") Double minStrike,
        @Param("maxStrike") Double maxStrike,
        @Param("timestamp") LocalDateTime timestamp
    );
}
```

### **4. DTO Classes**

#### **SmartMoneySignalResponse.java**
```java
@Data
@JsonInclude(JsonInclude.Include.NON_NULL)
public class SmartMoneySignalResponse {
    
    private String symbol;
    private String timestamp;
    private MarketBias bias;
    private Double confidence;
    private SmartMoneyMetrics metrics;
    private List<String> reasoning;
    
    @Data
    public static class SmartMoneyMetrics {
        private Double putCallRatio;
        private Double pcrShift;
        private Double atmStraddle;
        private Double straddleChangePercent;
        private Double openInterestAcceleration;
        private String ivRegime;
    }
}
```

#### **BiasAnalysis.java**
```java
@Data
public class BiasAnalysis {
    private MarketBias bias;
    private Double confidence;
    private List<String> reasoning;
    private Integer bullishSignals;
    private Integer bearishSignals;
    private Map<String, Object> featureContributions;
}
```

### **5. Service Layer**

#### **SmartMoneyService.java (Interface)**
```java
@Service
public interface SmartMoneyService {
    
    /**
     * Generate smart money signal for a symbol
     */
    SmartMoneySignalResponse generateSmartMoneySignal(String symbol) throws SmartMoneyException;
    
    /**
     * Get cached signal if available
     */
    Optional<SmartMoneySignalResponse> getCachedSignal(String symbol);
    
    /**
     * Clear cache for symbol
     */
    void clearCache(String symbol);
    
    /**
     * Validate symbol
     */
    boolean isValidSymbol(String symbol);
}
```

#### **SmartMoneyServiceImpl.java**
```java
@Service
@Transactional(readOnly = true)
@Slf4j
public class SmartMoneyServiceImpl implements SmartMoneyService {
    
    private static final int SNAPSHOT_COUNT = 30;
    private static final Duration CACHE_TTL = Duration.ofSeconds(30);
    private static final Set<String> VALID_SYMBOLS = Set.of("NIFTY", "BANKNIFTY");
    
    private final OptionChainSnapshotRepository snapshotRepository;
    private final SmartMoneyCalculationService calculationService;
    private final CacheManager cacheManager;
    
    public SmartMoneyServiceImpl(
            OptionChainSnapshotRepository snapshotRepository,
            SmartMoneyCalculationService calculationService,
            CacheManager cacheManager) {
        this.snapshotRepository = snapshotRepository;
        this.calculationService = calculationService;
        this.cacheManager = cacheManager;
    }
    
    @Override
    @Cacheable(value = "smartMoneySignals", key = "#symbol")
    public SmartMoneySignalResponse generateSmartMoneySignal(String symbol) throws SmartMoneyException {
        try {
            log.info("Generating smart money signal for symbol: {}", symbol);
            
            // Validate symbol
            if (!isValidSymbol(symbol)) {
                throw new InvalidSymbolException(
                    String.format("Invalid symbol: %s. Must be NIFTY or BANKNIFTY", symbol));
            }
            
            // Get latest snapshots
            List<OptionChainSnapshot> snapshots = getLatestSnapshots(symbol);
            if (snapshots.isEmpty()) {
                return createClosedMarketResponse(symbol);
            }
            
            // Calculate features
            SmartMoneyFeatures features = calculationService.calculateFeatures(snapshots);
            
            // Generate bias and confidence
            BiasAnalysis biasAnalysis = calculationService.generateBias(features);
            
            // Create response
            SmartMoneySignalResponse response = buildResponse(symbol, features, biasAnalysis);
            
            log.info("Generated smart money signal for {}: {} (confidence: {})", 
                     symbol, biasAnalysis.getBias(), biasAnalysis.getConfidence());
            
            return response;
            
        } catch (Exception e) {
            log.error("Error generating smart money signal for {}: {}", symbol, e.getMessage(), e);
            throw new SmartMoneyException("Failed to generate smart money signal", e);
        }
    }
    
    private List<OptionChainSnapshot> getLatestSnapshots(String symbol) {
        Pageable pageable = PageRequest.of(0, SNAPSHOT_COUNT);
        List<LocalDateTime> timestamps = snapshotRepository.findLatestTimestamps(symbol, pageable);
        
        if (timestamps.isEmpty()) {
            return Collections.emptyList();
        }
        
        return snapshotRepository.findBySymbolAndTimestamps(symbol, timestamps);
    }
    
    private SmartMoneySignalResponse createClosedMarketResponse(String symbol) {
        SmartMoneySignalResponse response = new SmartMoneySignalResponse();
        response.setSymbol(symbol.toUpperCase());
        response.setTimestamp(LocalDateTime.now().toString());
        response.setBias(MarketBias.NEUTRAL);
        response.setConfidence(0.0);
        
        SmartMoneySignalResponse.SmartMoneyMetrics metrics = new SmartMoneySignalResponse.SmartMoneyMetrics();
        metrics.setPutCallRatio(0.0);
        metrics.setPcrShift(0.0);
        metrics.setAtmStraddle(0.0);
        metrics.setStraddleChangePercent(0.0);
        metrics.setOpenInterestAcceleration(0.0);
        metrics.setIvRegime("NORMAL");
        response.setMetrics(metrics);
        response.setReasoning(List.of("Market closed - insufficient data"));
        
        return response;
    }
}
```

#### **SmartMoneyCalculationService.java**
```java
@Service
@Transactional(readOnly = true)
@Slf4j
public class SmartMoneyCalculationService {
    
    // Thresholds (move to configuration)
    private static final double OI_ACCELERATION_THRESHOLD = 1000.0;
    private static final double PCR_SHIFT_THRESHOLD = 0.1;
    private static final double STRADDLE_CHANGE_THRESHOLD = 2.0;
    private static final double PCR_HIGH_THRESHOLD = 1.2;
    private static final double PCR_LOW_THRESHOLD = 0.8;
    
    /**
     * Calculate all features from option chain snapshots
     */
    public SmartMoneyFeatures calculateFeatures(List<OptionChainSnapshot> snapshots) {
        Map<LocalDateTime, List<OptionChainSnapshot>> snapshotsByTime = groupByTimestamp(snapshots);
        List<LocalDateTime> sortedTimestamps = snapshotsByTime.keySet().stream()
                .sorted(Comparator.reverseOrder())
                .collect(Collectors.toList());
        
        if (sortedTimestamps.size() < 2) {
            return calculateBasicFeatures(
                snapshotsByTime.get(sortedTimestamps.get(0)));
        }
        
        SmartMoneyFeatures currentFeatures = calculateBasicFeatures(
                snapshotsByTime.get(sortedTimestamps.get(0)));
        SmartMoneyFeatures previousFeatures = calculateBasicFeatures(
                snapshotsByTime.get(1));
        
        // Calculate time-based features
        currentFeatures.setPcrShift(calculatePcrShift(snapshotsByTime, sortedTimestamps));
        currentFeatures.setStraddleChangePercent(calculateStraddleChange(
                currentFeatures.getAtmStraddle(), previousFeatures.getAtmStraddle()));
        currentFeatures.setOpenInterestAcceleration(calculateOiAcceleration(
                snapshotsByTime.get(sortedTimestamps.get(0)),
                snapshotsByTime.get(sortedTimestamps.get(1))));
        currentFeatures.setIvRegime(calculateIvRegime(snapshotsByTime, sortedTimestamps));
        
        return currentFeatures;
    }
    
    /**
     * Generate directional bias and confidence
     */
    public BiasAnalysis generateBias(SmartMoneyFeatures features) {
        List<String> reasoning = new ArrayList<>();
        int bullishSignals = 0;
        int bearishSignals = 0;
        
        // OI acceleration analysis
        double oiAcceleration = features.getOpenInterestAcceleration();
        if (oiAcceleration > OI_ACCELERATION_THRESHOLD) {
            bullishSignals++;
            reasoning.add("Put OI increasing faster than Call OI");
        } else if (oiAcceleration < -OI_ACCELERATION_THRESHOLD) {
            bearishSignals++;
            reasoning.add("Call OI increasing faster than Put OI");
        }
        
        // PCR shift analysis
        double pcrShift = features.getPcrShift();
        if (pcrShift > PCR_SHIFT_THRESHOLD) {
            bullishSignals++;
            reasoning.add("PCR rising above recent average");
        } else if (pcrShift < -PCR_SHIFT_THRESHOLD) {
            bearishSignals++;
            reasoning.add("PCR falling below recent average");
        }
        
        // Straddle change analysis
        double straddleChange = features.getStraddleChangePercent();
        if (straddleChange > STRADDLE_CHANGE_THRESHOLD) {
            bullishSignals++;
            reasoning.add("ATM straddle expanding upward");
        } else if (straddleChange < -STRADDLE_CHANGE_THRESHOLD) {
            bearishSignals++;
            reasoning.add("ATM straddle expanding downward");
        }
        
        // PCR level analysis
        double pcr = features.getPutCallRatio();
        if (pcr > PCR_HIGH_THRESHOLD) {
            bullishSignals++;
            reasoning.add("High PCR indicating bullish sentiment");
        } else if (pcr < PCR_LOW_THRESHOLD) {
            bearishSignals++;
            reasoning.add("Low PCR indicating bearish sentiment");
        }
        
        // Determine bias
        MarketBias bias = determineBias(bullishSignals, bearishSignals);
        double confidence = calculateConfidence(bullishSignals, bearishSignals, features);
        
        if (bias == MarketBias.NEUTRAL) {
            reasoning.add("Mixed signals with no clear directional bias");
        }
        
        BiasAnalysis analysis = new BiasAnalysis();
        analysis.setBias(bias);
        analysis.setConfidence(confidence);
        analysis.setReasoning(reasoning);
        analysis.setBullishSignals(bullishSignals);
        analysis.setBearishSignals(bearishSignals);
        
        return analysis;
    }
    
    private MarketBias determineBias(int bullishSignals, int bearishSignals) {
        if (bullishSignals > bearishSignals) {
            return MarketBias.BULLISH;
        } else if (bearishSignals > bullishSignals) {
            return MarketBias.BEARISH;
        } else {
            return MarketBias.NEUTRAL;
        }
    }
    
    private double calculateConfidence(int bullishSignals, int bearishSignals, SmartMoneyFeatures features) {
        int totalSignals = bullishSignals + bearishSignals;
        int signalStrength = Math.abs(bullishSignals - bearishSignals);
        double baseConfidence = (signalStrength / Math.max(totalSignals, 1)) * 50;
        
        // Boost confidence based on feature magnitudes
        double confidenceBoost = 0;
        confidenceBoost += Math.min(Math.abs(features.getPcrShift()) * 20, 20);
        confidenceBoost += Math.min(Math.abs(features.getStraddleChangePercent()) * 5, 15);
        confidenceBoost += Math.min(Math.abs(features.getOpenInterestAcceleration()) / 100, 15);
        
        return Math.min(baseConfidence + confidenceBoost, 100);
    }
}
```

### **6. Controller Layer**

#### **SmartMoneyController.java**
```java
@RestController
@RequestMapping("/api/v1/analytics")
@Slf4j
@Validated
public class SmartMoneyController {
    
    private final SmartMoneyService smartMoneyService;
    
    public SmartMoneyController(SmartMoneyService smartMoneyService) {
        this.smartMoneyService = smartMoneyService;
    }
    
    @GetMapping("/smart-money/{symbol}")
    public ResponseEntity<SmartMoneySignalResponse> getSmartMoneySignal(
            @PathVariable @Pattern(regexp = "NIFTY|BANKNIFTY", message = "Symbol must be NIFTY or BANKNIFTY") String symbol) {
        
        try {
            SmartMoneySignalResponse response = smartMoneyService.generateSmartMoneySignal(symbol);
            return ResponseEntity.ok(response);
            
        } catch (InvalidSymbolException e) {
            log.warn("Invalid symbol requested: {}", symbol);
            return ResponseEntity.badRequest().build();
            
        } catch (SmartMoneyException e) {
            log.error("Error generating smart money signal for {}: {}", symbol, e.getMessage());
            return ResponseEntity.internalServerError().build();
        }
    }
    
    @GetMapping("/smart-money/{symbol}/cache/clear")
    public ResponseEntity<Void> clearSmartMoneyCache(@PathVariable String symbol) {
        smartMoneyService.clearCache(symbol);
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/smart-money/symbols")
    public ResponseEntity<Set<String>> getSupportedSymbols() {
        return ResponseEntity.ok(Set.of("NIFTY", "BANKNIFTY"));
    }
}
```

### **7. Exception Handling**

#### **GlobalExceptionHandler.java**
```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    @ExceptionHandler(InvalidSymbolException.class)
    public ResponseEntity<ErrorResponse> handleInvalidSymbol(InvalidSymbolException e) {
        ErrorResponse error = new ErrorResponse("INVALID_SYMBOL", e.getMessage());
        return ResponseEntity.badRequest().body(error);
    }
    
    @ExceptionHandler(InsufficientDataException.class)
    public ResponseEntity<ErrorResponse> handleInsufficientData(InsufficientDataException e) {
        ErrorResponse error = new ErrorResponse("INSUFFICIENT_DATA", e.getMessage());
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(error);
    }
    
    @ExceptionHandler(SmartMoneyException.class)
    public ResponseEntity<ErrorResponse> handleSmartMoneyException(SmartMoneyException e) {
        ErrorResponse error = new ErrorResponse("SMART_MONEY_ERROR", e.getMessage());
        return ResponseEntity.internalServerError().body(error);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(MethodArgumentNotValidException e) {
        List<String> errors = e.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .collect(Collectors.toList());
        
        ErrorResponse error = new ErrorResponse("VALIDATION_ERROR", "Validation failed", errors);
        return ResponseEntity.badRequest().body(error);
    }
}

@Data
@AllArgsConstructor
public class ErrorResponse {
    private String code;
    private String message;
    private List<String> details;
}
```

---

## 🚀 REST Endpoint Mapping

### **Python Endpoint → Spring Boot Endpoint**

| Python Route | Spring Boot Route | Method | Description |
|---------------|-------------------|---------|-------------|
| `/api/v1/options/smart-money/{symbol}` | `/api/v1/analytics/smart-money/{symbol}` | GET | Generate smart money signal |
| `/api/v1/options/smart-money-v2/{symbol}` | `/api/v1/analytics/smart-money-v2/{symbol}` | GET | Enhanced smart money signal |
| `/api/v1/options/smart-money/performance/{symbol}` | `/api/v1/analytics/smart-money/{symbol}/performance` | GET | Performance analytics |

### **Request/Response Examples**

#### **Request**
```http
GET /api/v1/analytics/smart-money/NIFTY
Content-Type: application/json
```

#### **Response**
```json
{
  "symbol": "NIFTY",
  "timestamp": "2026-02-20T14:30:00Z",
  "bias": "BULLISH",
  "confidence": 75.5,
  "metrics": {
    "putCallRatio": 1.25,
    "pcrShift": 0.15,
    "atmStraddle": 150.75,
    "straddleChangePercent": 3.2,
    "openInterestAcceleration": 1250.0,
    "ivRegime": "HIGH"
  },
  "reasoning": [
    "Put OI increasing faster than Call OI",
    "PCR rising above recent average",
    "High PCR indicating bullish sentiment"
  ]
}
```

---

## 🎯 Migration Benefits

### **Java Spring Boot Advantages**
1. **Type Safety** - Compile-time error detection
2. **Dependency Injection** - Better testability and modularity
3. **Transaction Management** - Automatic rollback handling
4. **Caching** - Spring Cache abstraction
5. **Validation** - Bean Validation annotations
6. **Exception Handling** - Centralized error management
7. **Monitoring** - Actuator endpoints
8. **Performance** - Connection pooling and optimization

### **Architectural Improvements**
1. **Separation of Concerns** - Clear layer boundaries
2. **Single Responsibility** - Focused classes
3. **Interface Segregation** - Contract-based design
4. **Dependency Inversion** - Abstraction over implementation
5. **Configuration Management** - Externalized properties
6. **Testability** - Mockable dependencies

---

## ✅ Migration Status

| Component | Status | Notes |
|-----------|---------|-------|
| Entity Classes | ✅ Designed | JPA annotations, proper relationships |
| Repository Layer | ✅ Designed | Custom queries, optimization |
| Service Layer | ✅ Designed | Interface + implementation |
| DTO Classes | ✅ Designed | Request/Response models |
| Controller Layer | ✅ Designed | REST endpoints, validation |
| Exception Handling | ✅ Designed | Global exception handler |
| Caching | ✅ Designed | Spring Cache abstraction |
| Validation | ✅ Designed | Bean Validation annotations |

**🎯 Complete Spring Boot architecture designed for Smart Money Engine migration with production-ready patterns and best practices.**
