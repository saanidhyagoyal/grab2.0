package com.gxs.bank.controller;

import com.gxs.bank.dto.request.CardApplyRequest;
import com.gxs.bank.dto.response.ApiResponse;
import com.gxs.bank.model.Card;
import com.gxs.bank.model.User;
import com.gxs.bank.service.CardService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/cards")
@RequiredArgsConstructor
public class CardController {

    private final CardService cardService;

    @PostMapping("/apply")
    public ResponseEntity<ApiResponse<Card>> apply(
            @AuthenticationPrincipal User user,
            @Valid @RequestBody CardApplyRequest request) {
        Card card = cardService.applyForCard(user.getId(), request);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.ok("Card application submitted for approval", card));
    }

    @GetMapping
    public ResponseEntity<ApiResponse<List<Card>>> getCards(@AuthenticationPrincipal User user) {
        List<Card> cards = cardService.getUserCards(user.getId());
        return ResponseEntity.ok(ApiResponse.ok(cards));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Card>> getCard(
            @PathVariable UUID id, @AuthenticationPrincipal User user) {
        Card card = cardService.getCard(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok(card));
    }

    @PutMapping("/{id}/freeze")
    public ResponseEntity<ApiResponse<Card>> toggleFreeze(
            @PathVariable UUID id, @AuthenticationPrincipal User user) {
        Card card = cardService.toggleFreeze(id, user.getId());
        return ResponseEntity.ok(ApiResponse.ok("Card status updated", card));
    }

    @PutMapping("/{id}/settings")
    public ResponseEntity<ApiResponse<Card>> updateSettings(
            @PathVariable UUID id,
            @AuthenticationPrincipal User user,
            @RequestBody Map<String, Object> settings) {
        Card card = cardService.updateSettings(id, user.getId(), settings);
        return ResponseEntity.ok(ApiResponse.ok("Card settings updated", card));
    }
}
