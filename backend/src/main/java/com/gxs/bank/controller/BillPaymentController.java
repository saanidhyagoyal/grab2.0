package com.gxs.bank.controller;

import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.BillPayment;
import com.gxs.bank.model.User;
import com.gxs.bank.service.BillPaymentService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/bills")
@RequiredArgsConstructor
public class BillPaymentController {
    private final BillPaymentService billPaymentService;

    @PostMapping("/pay")
    public ResponseEntity<ApiResponse<BillPayment>> payBill(@AuthenticationPrincipal User user, @RequestBody Map<String, Object> payload) {
        BillPayment request = new BillPayment();
        request.setBillerName((String) payload.get("billerName"));
        request.setBillerCategory(BillPayment.BillerCategory.valueOf((String) payload.get("billerCategory")));
        String billerAccNo = (String) payload.get("billerAccountNumber");
        if (billerAccNo == null) billerAccNo = (String) payload.get("consumerNumber");
        request.setBillerAccountNumber(billerAccNo != null ? billerAccNo : "N/A");
        request.setAmount(new java.math.BigDecimal(payload.get("amount").toString()));
        UUID accountId = UUID.fromString((String) payload.get("accountId"));
        
        BillPayment payment = billPaymentService.payBill(user.getId(), accountId, request);
        return ResponseEntity.ok(ApiResponse.ok("Bill payment successful", payment));
    }

    @GetMapping("/history")
    public ResponseEntity<ApiResponse<List<BillPayment>>> getHistory(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(billPaymentService.getHistory(user.getId())));
    }

    @GetMapping("/billers")
    public ResponseEntity<ApiResponse<List<String>>> getBillers() {
        List<String> categories = Arrays.stream(BillPayment.BillerCategory.values()).map(Enum::name).toList();
        return ResponseEntity.ok(ApiResponse.ok(categories));
    }
}
