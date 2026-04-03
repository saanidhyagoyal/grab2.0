package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "bill_payments")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BillPayment {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore
    private User user;

    @Column(name = "biller_name", nullable = false)
    private String billerName;

    @Enumerated(EnumType.STRING)
    @Column(name = "biller_category", nullable = false)
    private BillerCategory billerCategory;

    @Column(name = "biller_account_number", nullable = false)
    private String billerAccountNumber;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status;

    @Column(name = "transaction_ref")
    private String transactionRef;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (status == null) status = Status.PENDING;
    }

    public enum BillerCategory { ELECTRICITY, GAS, WATER, DTH, BROADBAND, MOBILE_POSTPAID, INSURANCE_PREMIUM, CREDIT_CARD, MUNICIPAL_TAX, LOAN_EMI }
    public enum Status { PENDING, SUCCESS, FAILED }
}
