package com.gxs.bank.service;

import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.FixedDeposit;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.AccountRepository;
import com.gxs.bank.repository.FixedDepositRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class FixedDepositService {
    private final FixedDepositRepository fixedDepositRepository;
    private final UserRepository userRepository;
    private final AccountRepository accountRepository;

    @Transactional
    public FixedDeposit createFD(UUID userId, FixedDeposit request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));
        SavingsAccount source = accountRepository.findById(request.getSourceAccount().getId())
                .orElseThrow(() -> new ResourceNotFoundException("Source account not found"));

        if (!source.getUser().getId().equals(userId)) {
            throw new BadRequestException("Unauthorized");
        }
        if (source.getBalance().compareTo(request.getPrincipalAmount()) < 0) {
            throw new BadRequestException("Insufficient balance");
        }

        source.setBalance(source.getBalance().subtract(request.getPrincipalAmount()));
        accountRepository.save(source);

        request.setUser(user);
        request.setSourceAccount(source);
        request.setMaturityDate(LocalDate.now().plusMonths(request.getTenureMonths()));

        // Simple interest: P * r * t / 100
        BigDecimal interest = request.getPrincipalAmount()
                .multiply(request.getInterestRate())
                .multiply(BigDecimal.valueOf(request.getTenureMonths()))
                .divide(new BigDecimal("1200"), 2, java.math.RoundingMode.HALF_UP);

        request.setMaturityAmount(request.getPrincipalAmount().add(interest));
        request.setStatus(FixedDeposit.Status.ACTIVE);

        return fixedDepositRepository.save(request);
    }

    public List<FixedDeposit> getFDs(UUID userId) {
        return fixedDepositRepository.findByUserId(userId);
    }

    @Transactional
    public FixedDeposit breakFD(UUID fdId, UUID userId) {
        FixedDeposit fd = fixedDepositRepository.findById(fdId)
                .orElseThrow(() -> new ResourceNotFoundException("Fixed Deposit not found"));
        if (!fd.getUser().getId().equals(userId)) {
            throw new BadRequestException("Unauthorized");
        }
        if (fd.getStatus() != FixedDeposit.Status.ACTIVE) {
            throw new BadRequestException("FD is not active");
        }

        // Apply 1% penalty on principal
        BigDecimal penalty = fd.getPrincipalAmount().multiply(new BigDecimal("0.01"));
        BigDecimal refund = fd.getPrincipalAmount().subtract(penalty);

        SavingsAccount source = fd.getSourceAccount();
        source.setBalance(source.getBalance().add(refund));
        accountRepository.save(source);

        fd.setStatus(FixedDeposit.Status.BROKEN);
        return fixedDepositRepository.save(fd);
    }
}
