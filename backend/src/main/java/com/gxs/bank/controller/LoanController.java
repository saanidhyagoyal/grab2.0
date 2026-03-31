package com.gxs.bank.controller;

import com.gxs.bank.dto.request.LoanApplyRequest;
import com.gxs.bank.dto.request.LoanRepayRequest;
import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.Loan;
import com.gxs.bank.model.User;
import com.gxs.bank.service.LoanService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/loans")
@RequiredArgsConstructor
public class LoanController {

    private final LoanService loanService;

    @PostMapping("/apply")
    public ResponseEntity<ApiResponse<Loan>> apply(
            @AuthenticationPrincipal User user,
            @Valid @RequestBody LoanApplyRequest request) {
        Loan loan = loanService.applyForLoan(user.getId(), request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Loan approved", loan));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<Loan>>> getLoans(@AuthenticationPrincipal User user) {
        List<Loan> loans = loanService.getUserLoans(user.getId());
        return ResponseEntity.ok(ApiResponse.ok(loans));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Loan>> getLoan(
            @PathVariable UUID id, @AuthenticationPrincipal User user) {
        Loan loan = loanService.getLoan(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok(loan));
    }

    @PostMapping("/{id}/repay")
    public ResponseEntity<ApiResponse<Loan>> repay(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @Valid @RequestBody LoanRepayRequest request) {
        Loan loan = loanService.repay(id, user.getId(), request);
        return ResponseEntity.ok(ApiResponse.ok("Repayment processed", loan));
    }

    @GetMapping("/calculate")
    public ResponseEntity<ApiResponse<Map<String, Object>>> calculate(
            @RequestParam BigDecimal amount,
            @RequestParam(defaultValue = "1.08") BigDecimal rate,
            @RequestParam int tenureMonths) {
        Map<String, Object> result = loanService.calculateLoan(amount, rate, tenureMonths);
        return ResponseEntity.ok(ApiResponse.ok(result));
    }
}
