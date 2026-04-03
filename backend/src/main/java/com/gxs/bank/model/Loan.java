package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "loans")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Loan {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "loan_type", nullable = false)
    private LoanType loanType;

    @Column(name = "loan_name")
    private String loanName;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;

    @Column(name = "outstanding_amount", precision = 15, scale = 2)
    private BigDecimal outstandingAmount;

    @Column(name = "interest_rate", nullable = false, precision = 5, scale = 2)
    private BigDecimal interestRate;

    @Column(name = "tenure_months", nullable = false)
    private Integer tenureMonths;

    @Column(name = "monthly_payment", precision = 15, scale = 2)
    private BigDecimal monthlyPayment;

    @Column(name = "total_emis")
    private Integer totalEmis;

    @Column(name = "emis_paid")
    private Integer emisPaid;

    @Column(name = "next_emi_date")
    private LocalDate nextEmiDate;

    @Column(name = "processing_fee", precision = 15, scale = 2)
    private BigDecimal processingFee;

    @Column(name = "purpose")
    private String purpose;

    @Column(name = "applied_by")
    private UUID appliedBy;

    @Column(name = "approved_by")
    private UUID approvedBy;

    @Column(name = "approved_at")
    private LocalDateTime approvedAt;

    @Column(name = "disbursed_account_id")
    private UUID disbursedAccountId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (status == null) status = Status.PENDING;
        if (outstandingAmount == null) outstandingAmount = amount;
        if (totalEmis == null) totalEmis = tenureMonths;
        if (emisPaid == null) emisPaid = 0;
        if (processingFee == null) processingFee = BigDecimal.ZERO;
    }

    public enum LoanType { PERSONAL, HOME, VEHICLE, EDUCATION, GOLD, BUSINESS, BALANCE_TRANSFER, INSTALMENT }
    public enum Status { PENDING, ACTIVE, PAID_OFF, DEFAULTED, REJECTED }
}
