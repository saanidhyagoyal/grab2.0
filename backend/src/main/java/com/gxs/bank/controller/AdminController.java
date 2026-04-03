package com.gxs.bank.controller;

import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.AuditLog;
import com.gxs.bank.model.Card;
import com.gxs.bank.model.Loan;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.CardRepository;
import com.gxs.bank.repository.LoanRepository;
import com.gxs.bank.repository.UserRepository;
import com.gxs.bank.service.AuditLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin")
@PreAuthorize("hasRole('EMPLOYEE')")
@RequiredArgsConstructor
public class AdminController {
    private final CardRepository cardRepository;
    private final LoanRepository loanRepository;
    private final UserRepository userRepository;
    private final AuditLogService auditLogService;

    @GetMapping("/pending-approvals")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getPendingApprovals() {
        return ResponseEntity.ok(ApiResponse.ok(Map.of(
            "cards", cardRepository.findByStatus(Card.Status.PENDING),
            "loans", loanRepository.findByStatus(Loan.Status.PENDING),
            "kyc", userRepository.findByKycStatus(User.KycStatus.PENDING_REVIEW)
        )));
    }

    // Individual endpoints that the frontend API client expects
    @GetMapping("/pending-cards")
    public ResponseEntity<ApiResponse<List<Card>>> getPendingCards() {
        return ResponseEntity.ok(ApiResponse.ok(cardRepository.findByStatus(Card.Status.PENDING)));
    }

    @GetMapping("/pending-loans")
    public ResponseEntity<ApiResponse<List<Loan>>> getPendingLoans() {
        return ResponseEntity.ok(ApiResponse.ok(loanRepository.findByStatus(Loan.Status.PENDING)));
    }

    @PostMapping("/cards/{id}/approve")
    public ResponseEntity<ApiResponse<String>> approveCard(@AuthenticationPrincipal User employee, @PathVariable UUID id) {
        Card card = cardRepository.findById(id).orElseThrow();
        card.setStatus(Card.Status.ACTIVE);
        card.setApprovedBy(employee.getId());
        card.setApprovedAt(LocalDateTime.now());
        cardRepository.save(card);
        auditLogService.logAction(employee.getId(), AuditLog.Action.CARD_APPROVED, "CARD", id, "Approved card");
        return ResponseEntity.ok(ApiResponse.ok("Card approved"));
    }

    @PostMapping("/cards/{id}/reject")
    public ResponseEntity<ApiResponse<String>> rejectCard(@AuthenticationPrincipal User employee, @PathVariable UUID id) {
        Card card = cardRepository.findById(id).orElseThrow();
        card.setStatus(Card.Status.REJECTED);
        card.setApprovedBy(employee.getId());
        card.setApprovedAt(LocalDateTime.now());
        cardRepository.save(card);
        auditLogService.logAction(employee.getId(), AuditLog.Action.CARD_APPROVED, "CARD", id, "Rejected card");
        return ResponseEntity.ok(ApiResponse.ok("Card rejected"));
    }

    @PostMapping("/loans/{id}/approve")
    public ResponseEntity<ApiResponse<String>> approveLoan(@AuthenticationPrincipal User employee, @PathVariable UUID id) {
        Loan loan = loanRepository.findById(id).orElseThrow();
        loan.setStatus(Loan.Status.ACTIVE);
        loan.setApprovedBy(employee.getId());
        loan.setApprovedAt(LocalDateTime.now());
        loanRepository.save(loan);
        auditLogService.logAction(employee.getId(), AuditLog.Action.LOAN_APPROVED, "LOAN", id, "Approved loan");
        return ResponseEntity.ok(ApiResponse.ok("Loan approved"));
    }

    @PostMapping("/loans/{id}/reject")
    public ResponseEntity<ApiResponse<String>> rejectLoan(@AuthenticationPrincipal User employee, @PathVariable UUID id) {
        Loan loan = loanRepository.findById(id).orElseThrow();
        loan.setStatus(Loan.Status.REJECTED);
        loan.setApprovedBy(employee.getId());
        loan.setApprovedAt(LocalDateTime.now());
        loanRepository.save(loan);
        auditLogService.logAction(employee.getId(), AuditLog.Action.LOAN_APPROVED, "LOAN", id, "Rejected loan");
        return ResponseEntity.ok(ApiResponse.ok("Loan rejected"));
    }

    @GetMapping("/audit-logs")
    public ResponseEntity<ApiResponse<List<AuditLog>>> getAuditLogs() {
        return ResponseEntity.ok(ApiResponse.ok(auditLogService.getAllLogs()));
    }
}
