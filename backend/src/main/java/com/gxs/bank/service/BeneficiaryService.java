package com.gxs.bank.service;

import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.Beneficiary;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.BeneficiaryRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class BeneficiaryService {
    private final BeneficiaryRepository beneficiaryRepository;
    private final UserRepository userRepository;

    public Beneficiary addBeneficiary(UUID userId, Beneficiary request) {
        User user = userRepository.findById(userId).orElseThrow(() -> new ResourceNotFoundException("User not found"));
        request.setUser(user);
        return beneficiaryRepository.save(request);
    }

    public List<Beneficiary> getUserBeneficiaries(UUID userId) {
        return beneficiaryRepository.findByUserId(userId);
    }

    public void deleteBeneficiary(UUID id, UUID userId) {
        Beneficiary beneficiary = beneficiaryRepository.findById(id).orElseThrow(() -> new ResourceNotFoundException("Beneficiary not found"));
        if (!beneficiary.getUser().getId().equals(userId)) {
            throw new RuntimeException("Unauthorized");
        }
        beneficiaryRepository.delete(beneficiary);
    }
}
