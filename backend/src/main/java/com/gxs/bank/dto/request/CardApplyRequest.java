package com.gxs.bank.dto.request;

import jakarta.validation.constraints.*;
import lombok.*;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class CardApplyRequest {

    @NotBlank(message = "Card type is required (DEBIT or FLEXI)")
    private String cardType;
}
