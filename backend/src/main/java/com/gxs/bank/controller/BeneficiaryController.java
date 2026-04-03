package com.gxs.bank.controller;

import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.Beneficiary;
import com.gxs.bank.model.User;
import com.gxs.bank.service.BeneficiaryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/beneficiaries")
@RequiredArgsConstructor
public class BeneficiaryController {
    private final BeneficiaryService beneficiaryService;

    @PostMapping
    public ResponseEntity<ApiResponse<Beneficiary>> addBeneficiary(@AuthenticationPrincipal User user, @RequestBody Beneficiary request) {
        Beneficiary ben = beneficiaryService.addBeneficiary(user.getId(), request);
        return ResponseEntity.ok(ApiResponse.ok("Beneficiary added successfully", ben));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<Beneficiary>>> getBeneficiaries(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(beneficiaryService.getUserBeneficiaries(user.getId())));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<String>> deleteBeneficiary(@AuthenticationPrincipal User user, @PathVariable UUID id) {
        beneficiaryService.deleteBeneficiary(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok("Beneficiary deleted successfully"));
    }
}
