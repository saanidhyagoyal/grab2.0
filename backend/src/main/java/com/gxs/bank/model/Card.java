package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "cards")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Card {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore
    private User user;

    @Column(name = "card_number_last4", nullable = false, length = 4)
    private String cardNumberLast4;

    @Column(name = "card_holder_name")
    private String cardHolderName;

    @Enumerated(EnumType.STRING)
    @Column(name = "card_type", nullable = false)
    private CardType cardType;

    @Enumerated(EnumType.STRING)
    @Column(name = "card_network")
    private CardNetwork cardNetwork;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status;

    @Column(name = "expiry_date")
    private LocalDate expiryDate;

    @Column(name = "credit_limit", precision = 15, scale = 2)
    private BigDecimal creditLimit;

    @Column(name = "current_balance", precision = 15, scale = 2)
    private BigDecimal currentBalance;

    @Column(name = "cashback_earned", precision = 15, scale = 2)
    private BigDecimal cashbackEarned;

    @Column(name = "daily_limit", precision = 15, scale = 2)
    private BigDecimal dailyLimit;

    @Column(name = "monthly_limit", precision = 15, scale = 2)
    private BigDecimal monthlyLimit;

    @Column(name = "is_international_enabled")
    private Boolean isInternationalEnabled;

    @Column(name = "is_online_enabled")
    private Boolean isOnlineEnabled;

    @Column(name = "is_contactless_enabled")
    private Boolean isContactlessEnabled;

    @Column(name = "applied_by")
    private UUID appliedBy;

    @Column(name = "approved_by")
    private UUID approvedBy;

    @Column(name = "approved_at")
    private LocalDateTime approvedAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (currentBalance == null) currentBalance = BigDecimal.ZERO;
        if (cashbackEarned == null) cashbackEarned = BigDecimal.ZERO;
        if (status == null) status = Status.PENDING;
        if (dailyLimit == null) dailyLimit = new BigDecimal("50000.00");
        if (monthlyLimit == null) monthlyLimit = new BigDecimal("500000.00");
        if (isInternationalEnabled == null) isInternationalEnabled = false;
        if (isOnlineEnabled == null) isOnlineEnabled = true;
        if (isContactlessEnabled == null) isContactlessEnabled = true;
        if (expiryDate == null) expiryDate = LocalDate.now().plusYears(5);
    }

    public enum CardType { DEBIT, CREDIT, PREPAID, FLEXI }
    public enum CardNetwork { VISA, MASTERCARD, RUPAY }
    public enum Status { PENDING, ACTIVE, FROZEN, CANCELLED, REJECTED }
}
