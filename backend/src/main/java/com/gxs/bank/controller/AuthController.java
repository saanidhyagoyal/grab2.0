package com.gxs.bank.controller;

import com.gxs.bank.dto.request.LoginRequest;
import com.gxs.bank.dto.request.RegisterRequest;
import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.dto.response.AuthResponse;
import com.gxs.bank.model.User;
import com.gxs.bank.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponse>> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Registration successful", response));
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request);
        return ResponseEntity.ok(ApiResponse.ok("Login successful", response));
    }

    @GetMapping("/me")
    public ResponseEntity<ApiResponse<Map<String, Object>>> getProfile(@AuthenticationPrincipal User user) {
        // Re-fetch from DB to get the absolute latest state (e.g. after KYC approval)
        User fresh = authService.getUserById(user.getId());
        Map<String, Object> profile = new HashMap<>();
        profile.put("id", fresh.getId());
        profile.put("userId", fresh.getId());
        profile.put("fullName", fresh.getFullName());
        profile.put("email", fresh.getEmail());
        profile.put("phone", fresh.getPhone());
        profile.put("role", fresh.getRole().name());
        profile.put("employeeId", fresh.getEmployeeId());
        profile.put("department", fresh.getDepartment());
        profile.put("kycStatus", fresh.getKycStatus() != null ? fresh.getKycStatus().name() : "UNVERIFIED");
        profile.put("employeeRole", fresh.getEmployeeRole() != null ? fresh.getEmployeeRole().name() : null);
        profile.put("onboardingStatus", fresh.getOnboardingStatus() != null ? fresh.getOnboardingStatus().name() : null);
        profile.put("createdAt", fresh.getCreatedAt());
        // Personal details for profile page
        profile.put("dateOfBirth", fresh.getDateOfBirth());
        profile.put("gender", fresh.getGender() != null ? fresh.getGender().name() : null);
        profile.put("address", fresh.getAddress());
        profile.put("city", fresh.getCity());
        profile.put("state", fresh.getState());
        profile.put("pincode", fresh.getPincode());
        profile.put("panNumber", fresh.getPanNumber());
        profile.put("aadhaarLast4", fresh.getAadhaarLast4());
        profile.put("nomineeName", fresh.getNomineeName());
        profile.put("nomineeRelation", fresh.getNomineeRelation());
        return ResponseEntity.ok(ApiResponse.ok(profile));
    }
}
