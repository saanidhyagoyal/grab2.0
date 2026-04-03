package com.gxs.bank.service;

import com.gxs.bank.dto.request.LoanApplyRequest;
import com.gxs.bank.dto.request.LoanRepayRequest;
import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.Loan;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.LoanRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class LoanService {

    private final LoanRepository loanRepository;
    private final UserRepository userRepository;

    @Transactional
    public Loan applyForLoan(UUID userId, LoanApplyRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Loan.LoanType loanType;
        try {
            loanType = Loan.LoanType.valueOf(request.getLoanType().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("Invalid loan type. Must be one of: PERSONAL, HOME, VEHICLE, EDUCATION, GOLD, BUSINESS, INSTALMENT, BALANCE_TRANSFER");
        }

        BigDecimal interestRate = switch (loanType) {
            case BALANCE_TRANSFER -> BigDecimal.ZERO;
            case HOME -> new BigDecimal("8.50");
            case VEHICLE -> new BigDecimal("7.50");
            case EDUCATION -> new BigDecimal("5.00");
            case GOLD -> new BigDecimal("7.00");
            case BUSINESS -> new BigDecimal("10.00");
            default -> new BigDecimal("1.08"); // PERSONAL, INSTALMENT
        };

        BigDecimal monthlyPayment = calculateMonthlyPayment(
                request.getAmount(), interestRate, request.getTenureMonths());

        Loan loan = Loan.builder()
                .user(user)
                .loanType(loanType)
                .amount(request.getAmount())
                .outstandingAmount(request.getAmount())
                .interestRate(interestRate)
                .tenureMonths(request.getTenureMonths())
                .loanName(request.getLoanName())
                .monthlyPayment(monthlyPayment)
                .status(Loan.Status.PENDING)
                .build();

        return loanRepository.save(loan);
    }

    public List<Loan> getUserLoans(UUID userId) {
        return loanRepository.findByUserId(userId);
    }

    public Loan getLoan(UUID loanId, UUID userId) {
        Loan loan = loanRepository.findById(loanId)
                .orElseThrow(() -> new ResourceNotFoundException("Loan not found"));
        if (!loan.getUser().getId().equals(userId)) {
            throw new BadRequestException("Loan does not belong to user");
        }
        return loan;
    }

    @Transactional
    public Loan repay(UUID loanId, UUID userId, LoanRepayRequest request) {
        Loan loan = getLoan(loanId, userId);

        if (loan.getStatus() == Loan.Status.PAID_OFF) {
            throw new BadRequestException("Loan is already paid off");
        }

        BigDecimal newOutstanding = loan.getOutstandingAmount().subtract(request.getAmount());
        if (newOutstanding.compareTo(BigDecimal.ZERO) <= 0) {
            loan.setOutstandingAmount(BigDecimal.ZERO);
            loan.setStatus(Loan.Status.PAID_OFF);
        } else {
            loan.setOutstandingAmount(newOutstanding);
        }

        return loanRepository.save(loan);
    }

    public Map<String, Object> calculateLoan(BigDecimal amount, BigDecimal rate, int tenureMonths) {
        BigDecimal monthlyPayment = calculateMonthlyPayment(amount, rate, tenureMonths);
        BigDecimal totalPayment = monthlyPayment.multiply(BigDecimal.valueOf(tenureMonths));
        BigDecimal totalInterest = totalPayment.subtract(amount);

        Map<String, Object> result = new HashMap<>();
        result.put("loanAmount", amount);
        result.put("interestRate", rate);
        result.put("tenureMonths", tenureMonths);
        result.put("monthlyPayment", monthlyPayment);
        result.put("totalPayment", totalPayment);
        result.put("totalInterest", totalInterest);
        return result;
    }

    private BigDecimal calculateMonthlyPayment(BigDecimal principal, BigDecimal annualRate, int tenureMonths) {
        if (annualRate.compareTo(BigDecimal.ZERO) == 0) {
            return principal.divide(BigDecimal.valueOf(tenureMonths), 2, RoundingMode.HALF_UP);
        }
        BigDecimal monthlyRate = annualRate.divide(BigDecimal.valueOf(1200), 10, RoundingMode.HALF_UP);
        BigDecimal onePlusR = BigDecimal.ONE.add(monthlyRate);
        BigDecimal power = onePlusR.pow(tenureMonths, MathContext.DECIMAL128);
        BigDecimal numerator = principal.multiply(monthlyRate).multiply(power);
        BigDecimal denominator = power.subtract(BigDecimal.ONE);
        return numerator.divide(denominator, 2, RoundingMode.HALF_UP);
    }
}
