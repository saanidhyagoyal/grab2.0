package com.gxs.bank.service;

import com.gxs.bank.dto.request.DepositRequest;
import com.gxs.bank.dto.request.TransferRequest;
import com.gxs.bank.dto.request.WithdrawRequest;
import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.Transaction;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.AccountRepository;
import com.gxs.bank.repository.TransactionRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.Random;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AccountService {

    private final AccountRepository accountRepository;
    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;

    @Transactional
    public SavingsAccount createAccount(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        if (user.getKycStatus() != User.KycStatus.VERIFIED) {
            throw new BadRequestException("KYC must be verified before opening an account. Current status: " + user.getKycStatus());
        }

        String accountNumber = generateAccountNumber();

        SavingsAccount account = SavingsAccount.builder()
                .user(user)
                .accountNumber(accountNumber)
                .balance(BigDecimal.ZERO)
                .interestRate(new BigDecimal("2.08"))
                .status(SavingsAccount.Status.ACTIVE)
                .build();

        return accountRepository.save(account);
    }

    public List<SavingsAccount> getUserAccounts(UUID userId) {
        return accountRepository.findByUserId(userId);
    }

    public SavingsAccount getAccount(UUID accountId, UUID userId) {
        SavingsAccount account = accountRepository.findById(accountId)
                .orElseThrow(() -> new ResourceNotFoundException("Account not found"));
        if (!account.getUser().getId().equals(userId)) {
            throw new BadRequestException("Account does not belong to user");
        }
        return account;
    }

    @Transactional
    public Transaction deposit(UUID accountId, UUID userId, DepositRequest request) {
        SavingsAccount account = getAccount(accountId, userId);
        account.setBalance(account.getBalance().add(request.getAmount()));
        accountRepository.save(account);

        Transaction txn = Transaction.builder()
                .account(account)
                .type(Transaction.Type.CREDIT)
                .amount(request.getAmount())
                .description(request.getDescription() != null ? request.getDescription() : "Deposit")
                .balanceAfter(account.getBalance())
                .channel(Transaction.Channel.NET_BANKING)
                .txnStatus(Transaction.TxnStatus.SUCCESS)
                .build();

        return transactionRepository.save(txn);
    }

    @Transactional
    public Transaction withdraw(UUID accountId, UUID userId, WithdrawRequest request) {
        SavingsAccount account = getAccount(accountId, userId);

        if (account.getBalance().compareTo(request.getAmount()) < 0) {
            throw new BadRequestException("Insufficient balance");
        }

        account.setBalance(account.getBalance().subtract(request.getAmount()));
        accountRepository.save(account);

        Transaction txn = Transaction.builder()
                .account(account)
                .type(Transaction.Type.DEBIT)
                .amount(request.getAmount())
                .description(request.getDescription() != null ? request.getDescription() : "Withdrawal")
                .balanceAfter(account.getBalance())
                .channel(Transaction.Channel.NET_BANKING)
                .txnStatus(Transaction.TxnStatus.SUCCESS)
                .build();

        return transactionRepository.save(txn);
    }

    @Transactional
    public Transaction transfer(UUID accountId, UUID userId, TransferRequest request) {
        SavingsAccount sourceAccount = getAccount(accountId, userId);
        if (sourceAccount.getStatus() != SavingsAccount.Status.ACTIVE) {
            throw new BadRequestException("Source account is not active");
        }

        SavingsAccount targetAccount = accountRepository.findByAccountNumber(request.getTargetAccountNumber())
                .orElseThrow(() -> new ResourceNotFoundException("Target account not found"));

        if (targetAccount.getStatus() != SavingsAccount.Status.ACTIVE) {
            throw new BadRequestException("Target account is not active");
        }

        if (sourceAccount.getBalance().compareTo(request.getAmount()) < 0) {
            throw new BadRequestException("Insufficient balance");
        }

        sourceAccount.setBalance(sourceAccount.getBalance().subtract(request.getAmount()));
        targetAccount.setBalance(targetAccount.getBalance().add(request.getAmount()));

        accountRepository.save(sourceAccount);
        accountRepository.save(targetAccount);

        String refNumber = "GXS" + System.currentTimeMillis();

        Transaction outTxn = Transaction.builder()
                .account(sourceAccount)
                .type(Transaction.Type.TRANSFER_OUT)
                .amount(request.getAmount())
                .description("Transfer to " + request.getTargetAccountNumber())
                .balanceAfter(sourceAccount.getBalance())
                .referenceNumber(refNumber + "OUT")
                .channel(Transaction.Channel.IMPS)
                .counterpartyName(targetAccount.getUser().getFullName())
                .counterpartyAccount(request.getTargetAccountNumber())
                .txnStatus(Transaction.TxnStatus.SUCCESS)
                .build();
        transactionRepository.save(outTxn);

        Transaction inTxn = Transaction.builder()
                .account(targetAccount)
                .type(Transaction.Type.TRANSFER_IN)
                .amount(request.getAmount())
                .description("Transfer from " + sourceAccount.getAccountNumber())
                .balanceAfter(targetAccount.getBalance())
                .referenceNumber(refNumber + "IN")
                .channel(Transaction.Channel.IMPS)
                .counterpartyName(sourceAccount.getUser().getFullName())
                .counterpartyAccount(sourceAccount.getAccountNumber())
                .txnStatus(Transaction.TxnStatus.SUCCESS)
                .build();
        transactionRepository.save(inTxn);

        return outTxn;
    }

    public Page<Transaction> getTransactions(UUID accountId, UUID userId, int page, int size) {
        getAccount(accountId, userId);
        return transactionRepository.findByAccountIdOrderByCreatedAtDesc(accountId, PageRequest.of(page, size));
    }

    public List<Transaction> getMiniStatement(UUID accountId, UUID userId) {
        getAccount(accountId, userId);
        return transactionRepository.findTop10ByAccountIdOrderByCreatedAtDesc(accountId);
    }

    private String generateAccountNumber() {
        Random random = new Random();
        String accountNumber;
        do {
            accountNumber = String.format("GXS%010d", random.nextLong(10_000_000_000L));
        } while (accountRepository.existsByAccountNumber(accountNumber));
        return accountNumber;
    }
}
