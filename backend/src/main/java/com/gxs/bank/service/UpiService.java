package com.gxs.bank.service;

import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.SavingsAccount;
import com.gxs.bank.model.UpiId;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.AccountRepository;
import com.gxs.bank.repository.UpiIdRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UpiService {
    private final UpiIdRepository upiIdRepository;
    private final UserRepository userRepository;
    private final AccountRepository accountRepository;

    public UpiId registerUpi(UUID userId, UUID accountId, String requestedId) {
        User user = userRepository.findById(userId).orElseThrow();
        SavingsAccount account = accountRepository.findById(accountId).orElseThrow();
        if (!account.getUser().getId().equals(userId)) throw new BadRequestException("Unauthorized");
        
        UpiId upi = UpiId.builder()
            .user(user)
            .account(account)
            .upiAddress(requestedId + "@gxs")
            .isPrimary(true)
            .isActive(true)
            .build();
        return upiIdRepository.save(upi);
    }
    
    public List<UpiId> getUserUpis(UUID userId) {
        return upiIdRepository.findByUserId(userId);
    }
}
