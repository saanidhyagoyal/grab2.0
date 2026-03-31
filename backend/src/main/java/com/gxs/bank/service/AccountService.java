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

    public SavingsAccount createAccount(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

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
                .build();

        return transactionRepository.save(txn);
    }

    @Transactional
    public Transaction transfer(UUID accountId, UUID userId, TransferRequest request) {
        SavingsAccount sourceAccount = getAccount(accountId, userId);
        SavingsAccount targetAccount = accountRepository.findByAccountNumber(request.getTargetAccountNumber())
                .orElseThrow(() -> new ResourceNotFoundException("Target account not found"));

        if (sourceAccount.getBalance().compareTo(request.getAmount()) < 0) {
            throw new BadRequestException("Insufficient balance");
        }

        sourceAccount.setBalance(sourceAccount.getBalance().subtract(request.getAmount()));
        targetAccount.setBalance(targetAccount.getBalance().add(request.getAmount()));
        accountRepository.save(sourceAccount);
        accountRepository.save(targetAccount);

        Transaction outTxn = Transaction.builder()
                .account(sourceAccount)
                .type(Transaction.Type.TRANSFER_OUT)
                .amount(request.getAmount())
                .description("Transfer to " + request.getTargetAccountNumber())
                .balanceAfter(sourceAccount.getBalance())
                .build();
        transactionRepository.save(outTxn);

        Transaction inTxn = Transaction.builder()
                .account(targetAccount)
                .type(Transaction.Type.TRANSFER_IN)
                .amount(request.getAmount())
                .description("Transfer from " + sourceAccount.getAccountNumber())
                .balanceAfter(targetAccount.getBalance())
                .build();
        transactionRepository.save(inTxn);

        return outTxn;
    }

    public Page<Transaction> getTransactions(UUID accountId, UUID userId, int page, int size) {
        getAccount(accountId, userId); // verify ownership
        return transactionRepository.findByAccountIdOrderByCreatedAtDesc(accountId, PageRequest.of(page, size));
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
