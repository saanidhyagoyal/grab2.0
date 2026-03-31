package com.gxs.bank.service;

import com.gxs.bank.dto.request.CardApplyRequest;
import com.gxs.bank.exception.BadRequestException;
import com.gxs.bank.exception.ResourceNotFoundException;
import com.gxs.bank.model.Card;
import com.gxs.bank.model.User;
import com.gxs.bank.repository.CardRepository;
import com.gxs.bank.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.Random;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CardService {

    private final CardRepository cardRepository;
    private final UserRepository userRepository;

    public Card applyForCard(UUID userId, CardApplyRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        Card.CardType cardType;
        try {
            cardType = Card.CardType.valueOf(request.getCardType().toUpperCase());
        } catch (IllegalArgumentException e) {
            throw new BadRequestException("Invalid card type. Must be DEBIT or FLEXI");
        }

        BigDecimal creditLimit = cardType == Card.CardType.FLEXI
                ? new BigDecimal("5000.00")
                : BigDecimal.ZERO;

        Card card = Card.builder()
                .user(user)
                .cardNumberLast4(String.format("%04d", new Random().nextInt(10000)))
                .cardType(cardType)
                .status(Card.Status.ACTIVE)
                .creditLimit(creditLimit)
                .currentBalance(BigDecimal.ZERO)
                .cashbackEarned(BigDecimal.ZERO)
                .build();

        return cardRepository.save(card);
    }

    public List<Card> getUserCards(UUID userId) {
        return cardRepository.findByUserId(userId);
    }

    public Card getCard(UUID cardId, UUID userId) {
        Card card = cardRepository.findById(cardId)
                .orElseThrow(() -> new ResourceNotFoundException("Card not found"));
        if (!card.getUser().getId().equals(userId)) {
            throw new BadRequestException("Card does not belong to user");
        }
        return card;
    }

    public Card toggleFreeze(UUID cardId, UUID userId) {
        Card card = getCard(cardId, userId);
        if (card.getStatus() == Card.Status.ACTIVE) {
            card.setStatus(Card.Status.FROZEN);
        } else if (card.getStatus() == Card.Status.FROZEN) {
            card.setStatus(Card.Status.ACTIVE);
        } else {
            throw new BadRequestException("Cannot toggle freeze on a cancelled card");
        }
        return cardRepository.save(card);
    }
}
