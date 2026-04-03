package com.gxs.bank.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "transactions")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Transaction {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "account_id", nullable = false)
    @JsonIgnore
    private SavingsAccount account;

    @Column(name = "account_id", insertable = false, updatable = false)
    private UUID accountId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Type type;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;

    @Column(nullable = false)
    private String description;

    @Column(name = "balance_after", nullable = false, precision = 15, scale = 2)
    private BigDecimal balanceAfter;

    @Column(name = "reference_number", unique = true)
    private String referenceNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "channel")
    private Channel channel;

    @Column(name = "counterparty_name")
    private String counterpartyName;

    @Column(name = "counterparty_account")
    private String counterpartyAccount;

    @Column(name = "remarks")
    private String remarks;

    @Enumerated(EnumType.STRING)
    @Column(name = "txn_status")
    private TxnStatus txnStatus;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        if (txnStatus == null) txnStatus = TxnStatus.SUCCESS;
        if (channel == null) channel = Channel.NET_BANKING;
        if (referenceNumber == null) referenceNumber = generateRef();
    }

    private String generateRef() {
        return "GXS" + System.currentTimeMillis() + (int)(Math.random() * 1000);
    }

    public enum Type { CREDIT, DEBIT, TRANSFER_IN, TRANSFER_OUT, INTEREST, UPI_CREDIT, UPI_DEBIT, EMI, ATM_WITHDRAWAL, POS_PURCHASE, BILL_PAYMENT, SALARY_CREDIT, FD_DEPOSIT, FD_MATURITY }
    public enum Channel { NET_BANKING, UPI, MOBILE, ATM, BRANCH, NEFT, RTGS, IMPS }
    public enum TxnStatus { SUCCESS, PENDING, FAILED, REVERSED }
}
