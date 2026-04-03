package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "upi_ids")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpiId {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "account_id", nullable = false)
    @JsonIgnoreProperties({"hibernateLazyInitializer", "handler"})
    private SavingsAccount account;

    @Column(name = "upi_address", nullable = false, unique = true)
    private String upiAddress;

    @Column(name = "is_primary")
    private Boolean isPrimary;

    @Column(name = "is_active")
    private Boolean isActive;

    @Column(name = "daily_limit", precision = 15, scale = 2)
    private BigDecimal dailyLimit;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (isPrimary == null) isPrimary = true;
        if (isActive == null) isActive = true;
        if (dailyLimit == null) dailyLimit = new BigDecimal("100000.00");
    }
}
