package com.gxs.bank.service;

import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.BillPayment;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.AccountRepository;
import com.gxs.bank.repository.BillPaymentRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class BillPaymentService {
    private final BillPaymentRepository billPaymentRepository;
    private final UserRepository userRepository;
    private final AccountService accountService;
    private final AccountRepository accountRepository;

    @Transactional
    public BillPayment payBill(UUID userId, UUID accountId, BillPayment request) {
        User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));
        SavingsAccount account = accountRepository.findById(accountId).orElseThrow(() -> new ResourceNotFoundException("Account not found"));
        
        if (!account.getUser().getId().equals(userId)) {
            throw new BadRequestException("Not your account");
        }
        if (account.getBalance().compareTo(request.getAmount()) < 0) {
            throw new BadRequestException("Insufficient balance");
        }
        
        account.setBalance(account.getBalance().subtract(request.getAmount()));
        accountRepository.save(account);
        
        request.setUser(user);
        request.setStatus(BillPayment.Status.SUCCESS);
        request.setTransactionRef("BP-GXS-" + System.currentTimeMillis());
        return billPaymentRepository.save(request);
    }

    public List<BillPayment> getHistory(UUID userId) {
        return billPaymentRepository.findByUserId(userId);
    }
}
