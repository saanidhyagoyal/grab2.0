package com.gxs.bank.controller;

import com.gxs.bank.dto.request.ContactRequest;
import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.ContactSubmission;
import com.gxs.bank.model.User;
import com.gxs.bank.service.ContactService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/contact")
@RequiredArgsConstructor
public class ContactController {

    private final ContactService contactService;

    @PostMapping
    public ResponseEntity<ApiResponse<ContactSubmission>> submit(@Valid @RequestBody ContactRequest request) {
        ContactSubmission submission = contactService.submit(request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Message sent successfully", submission));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<ContactSubmission>>> getSubmissions(
            @AuthenticationPrincipal User user) {
        List<ContactSubmission> submissions;
        if (user.getRole() == User.Role.EMPLOYEE) {
            submissions = contactService.getAll();
        } else {
            submissions = contactService.getByEmail(user.getEmail());
        }
        return ResponseEntity.ok(ApiResponse.ok(submissions));
    }
}
