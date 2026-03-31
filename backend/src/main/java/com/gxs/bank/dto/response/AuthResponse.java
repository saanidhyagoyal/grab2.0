package com.gxs.bank.dto.response;

import lombok.*;
import java.util.UUID;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor @Builder
public class AuthResponse {
    private String token;
    private String type;
    private UUID userId;
    private String fullName;
    private String email;
    private String role;
}
