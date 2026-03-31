package com.gxs.bank.controller;

import com.gxs.bank.dto.request.DepositRequest;
import com.gxs.bank.dto.request.TransferRequest;
import com.gxs.bank.dto.request.WithdrawRequest;
import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.Transaction;
import com.gxs.bank.model.User;
import com.gxs.bank.service.AccountService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {

    private final AccountService accountService;

    @PostMapping
    public ResponseEntity<ApiResponse<SavingsAccount>> createAccount(@AuthenticationPrincipal User user) {
        SavingsAccount account = accountService.createAccount(user.getId());
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Account created successfully", account));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<SavingsAccount>>> getAccounts(@AuthenticationPrincipal User user) {
        List<SavingsAccount> accounts = accountService.getUserAccounts(user.getId());
        return ResponseEntity.ok(ApiResponse.ok(accounts));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<SavingsAccount>> getAccount(
            @PathVariable UUID id, @AuthenticationPrincipal User user) {
        SavingsAccount account = accountService.getAccount(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok(account));
    }

    @GetMapping("/{id}/transactions")
    public ResponseEntity<ApiResponse<Page<Transaction>>> getTransactions(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Page<Transaction> transactions = accountService.getTransactions(id, user.getId(), page, size);
        return ResponseEntity.ok(ApiResponse.ok(transactions));
    }

    @PostMapping("/{id}/deposit")
    public ResponseEntity<ApiResponse<Transaction>> deposit(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @Valid @RequestBody DepositRequest request) {
        Transaction txn = accountService.deposit(id, user.getId(), request);
        return ResponseEntity.ok(ApiResponse.ok("Deposit successful", txn));
    }

    @PostMapping("/{id}/withdraw")
    public ResponseEntity<ApiResponse<Transaction>> withdraw(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @Valid @RequestBody WithdrawRequest request) {
        Transaction txn = accountService.withdraw(id, user.getId(), request);
        return ResponseEntity.ok(ApiResponse.ok("Withdrawal successful", txn));
    }

    @PostMapping("/{id}/transfer")
    public ResponseEntity<ApiResponse<Transaction>> transfer(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @Valid @RequestBody TransferRequest request) {
        Transaction txn = accountService.transfer(id, user.getId(), request);
        return ResponseEntity.ok(ApiResponse.ok("Transfer successful", txn));
    }
}
