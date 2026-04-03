package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "savings_accounts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SavingsAccount {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore
    private User user;

    @Column(name = "account_number", nullable = false, unique = true)
    private String accountNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "account_type", nullable = false)
    private AccountType accountType;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal balance;

    @Column(name = "interest_rate", nullable = false, precision = 5, scale = 2)
    private BigDecimal interestRate;

    @Column(name = "daily_interest_accrued", precision = 15, scale = 6)
    private BigDecimal dailyInterestAccrued;
    
    @Column(name = "ifsc_code", length = 11)
    private String ifscCode;

    @Column(name = "branch_name")
    private String branchName;

    @Column(name = "micr_code", length = 9)
    private String micrCode;

    @Column(name = "nominee_name")
    private String nomineeName;

    @Column(name = "daily_withdrawal_limit", precision = 15, scale = 2)
    private BigDecimal dailyWithdrawalLimit;

    @Column(name = "monthly_transfer_limit", precision = 15, scale = 2)
    private BigDecimal monthlyTransferLimit;

    @Column(name = "is_upi_enabled")
    private Boolean isUpiEnabled;

    @Column(name = "is_mobile_banking_enabled")
    private Boolean isMobileBankingEnabled;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (balance == null) balance = BigDecimal.ZERO;
        if (dailyInterestAccrued == null) dailyInterestAccrued = BigDecimal.ZERO;
        if (status == null) status = Status.ACTIVE;
        if (accountType == null) accountType = AccountType.SAVINGS;
        if (ifscCode == null) ifscCode = "GXSB0000001";
        if (branchName == null) branchName = "GXS Digital Branch";
        if (dailyWithdrawalLimit == null) dailyWithdrawalLimit = new BigDecimal("200000.00");
        if (monthlyTransferLimit == null) monthlyTransferLimit = new BigDecimal("1000000.00");
        if (isUpiEnabled == null) isUpiEnabled = true;
        if (isMobileBankingEnabled == null) isMobileBankingEnabled = true;
    }

    public enum AccountType { SAVINGS, CURRENT, FIXED_DEPOSIT, RECURRING_DEPOSIT }
    public enum Status { ACTIVE, FROZEN, CLOSED }
}
