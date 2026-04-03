package com.gxs.bank.dto.request;

import jakarta.validation.constraints.*;
import lombok.*;
import java.math.BigDecimal;

@Getter @Setter @NoArgsConstructor @AllArgsConstructor
public class LoanApplyRequest {

    @NotBlank(message = "Loan type is required (INSTALMENT or BALANCE_TRANSFER)")
    private String loanType;

    @NotNull(message = "Amount is required")
    @DecimalMin(value = "1000", message = "Minimum loan amount is S$1,000")
    private BigDecimal amount;

    @NotNull(message = "Tenure is required")
    @Min(value = 3, message = "Minimum tenure is 3 months")
    @Max(value = 360, message = "Maximum tenure is 360 months")
    private Integer tenureMonths;

    private String loanName; // e.g. "AIYAH", "IKEA"
}
