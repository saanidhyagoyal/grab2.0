package com.gxs.bank.service;

import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.Promotion;
import com.gxs.bank.repository.PromotionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class PromotionService {

    private final PromotionRepository promotionRepository;

    public List<Promotion> getActivePromotions() {
        return promotionRepository.findByIsActiveTrueOrderByValidFromDesc();
    }

    public Promotion getPromotion(UUID id) {
        return promotionRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Promotion not found"));
    }
}
