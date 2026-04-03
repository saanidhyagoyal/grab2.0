package com.gxs.bank.controller;

import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.FixedDeposit;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.User;
import com.gxs.bank.service.FixedDepositService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/fd")
@RequiredArgsConstructor
public class FixedDepositController {
    private final FixedDepositService fixedDepositService;

    @PostMapping("/create")
    public ResponseEntity<ApiResponse<FixedDeposit>> createFD(
            @AuthenticationPrincipal User user,
            @RequestBody Map<String, Object> payload) {

        String accountId = (String) payload.get("sourceAccountId");
        if (accountId == null) {
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("sourceAccountId is required"));
        }

        Object amtRaw = payload.get("principalAmount");
        Object rateRaw = payload.get("interestRate");
        Object tenureRaw = payload.get("tenureMonths");
        Object autoRenewRaw = payload.get("autoRenew");

        if (amtRaw == null || tenureRaw == null) {
            return ResponseEntity.badRequest()
                    .body(ApiResponse.error("principalAmount and tenureMonths are required"));
        }

        FixedDeposit fd = new FixedDeposit();
        fd.setPrincipalAmount(new BigDecimal(amtRaw.toString()));
        fd.setTenureMonths(Integer.parseInt(tenureRaw.toString()));

        // interest rate: use provided or calculate by tenure
        if (rateRaw != null) {
            fd.setInterestRate(new BigDecimal(rateRaw.toString()));
        } else {
            int tenure = fd.getTenureMonths();
            BigDecimal rate = tenure >= 36 ? new BigDecimal("7.25")
                    : tenure >= 24 ? new BigDecimal("7.00")
                    : tenure >= 12 ? new BigDecimal("6.50")
                    : new BigDecimal("5.50");
            fd.setInterestRate(rate);
        }

        fd.setAutoRenew(autoRenewRaw != null && Boolean.parseBoolean(autoRenewRaw.toString()));

        SavingsAccount sa = new SavingsAccount();
        sa.setId(UUID.fromString(accountId));
        fd.setSourceAccount(sa);

        FixedDeposit created = fixedDepositService.createFD(user.getId(), fd);
        return ResponseEntity.ok(ApiResponse.ok("Fixed Deposit created", created));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<FixedDeposit>>> getFDs(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(fixedDepositService.getFDs(user.getId())));
    }

    @PostMapping("/{id}/break")
    public ResponseEntity<ApiResponse<FixedDeposit>> breakFD(
            @AuthenticationPrincipal User user,
            @PathVariable UUID id) {
        FixedDeposit fd = fixedDepositService.breakFD(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok("Fixed Deposit broken, amount credited to account", fd));
    }
}
