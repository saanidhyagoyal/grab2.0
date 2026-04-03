package com.gxs.bank.controller;

import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.KycDocument;
import com.gxs.bank.model.User;
import com.gxs.bank.service.KycService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/kyc")
@RequiredArgsConstructor
public class KycController {
    private final KycService kycService;

    @PostMapping("/submit")
    public ResponseEntity<ApiResponse<KycDocument>> submitKyc(@AuthenticationPrincipal User user, @RequestBody Map<String, String> request) {
        KycDocument.DocumentType type = KycDocument.DocumentType.valueOf(request.get("documentType").toUpperCase());
        String documentNumber = request.get("documentNumber");
        String fileUrl = request.getOrDefault("fileUrl", "dummy_url");
        
        KycDocument doc = kycService.submitDocument(user.getId(), type, documentNumber, fileUrl);
        return ResponseEntity.ok(ApiResponse.ok("KYC submitted successfully", doc));
    }

    @GetMapping("/documents")
    public ResponseEntity<ApiResponse<List<KycDocument>>> getDocuments(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(kycService.getUserDocuments(user.getId())));
    }
}
