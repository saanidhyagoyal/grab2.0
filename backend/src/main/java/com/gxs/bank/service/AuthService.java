package com.gxs.bank.service;

import com.gxs.bank.dto.request.LoginRequest;
import com.gxs.bank.dto.request.RegisterRequest;
import com.gxs.bank.dto.response.AuthResponse;
import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.UserRepository;
import com.gxs.bank.security.JwtTokenProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;

    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BadRequestException("Email already registered");
        }

        User.Role role;
        try {
            role = User.Role.valueOf(request.getRole().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("Invalid role. Must be CUSTOMER or EMPLOYEE");
        }

        User.EmployeeRole employeeRole = null;
        if (role == User.Role.EMPLOYEE && request.getEmployeeRole() != null) {
            try {
                employeeRole = User.EmployeeRole.valueOf(request.getEmployeeRole().toUpperCase());
            } catch (IllegalArgumentException e) {
                throw new BadRequestException("Invalid employee role. Must be MAKER, CHECKER, or ADMIN");
            }
        }

        User user = User.builder()
                .fullName(request.getFullName())
                .email(request.getEmail())
                .phone(request.getPhone())
                .passwordHash(passwordEncoder.encode(request.getPassword()))
                .role(role)
                .employeeRole(employeeRole)
                .employeeId(request.getEmployeeId())
                .department(request.getDepartment())
                .build();

        user = userRepository.save(user);
        return buildAuthResponse(user);
    }

    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new BadRequestException("Invalid email or password"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new BadRequestException("Invalid email or password");
        }

        return buildAuthResponse(user);
    }

    public User getUserById(UUID userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
    }

    private AuthResponse buildAuthResponse(User user) {
        String token = tokenProvider.generateToken(user.getId(), user.getEmail(), user.getRole().name());

        return AuthResponse.builder()
                .token(token)
                .type("Bearer")
                .userId(user.getId())
                .fullName(user.getFullName())
                .email(user.getEmail())
                .phone(user.getPhone())
                .role(user.getRole().name())
                .kycStatus(user.getKycStatus() != null ? user.getKycStatus().name() : "UNVERIFIED")
                .employeeRole(user.getEmployeeRole() != null ? user.getEmployeeRole().name() : null)
                .department(user.getDepartment())
                .employeeId(user.getEmployeeId())
                .onboardingStatus(user.getOnboardingStatus() != null ? user.getOnboardingStatus().name() : null)
                .build();
    }
}
