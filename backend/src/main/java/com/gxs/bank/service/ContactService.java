package com.gxs.bank.service;

import com.gxs.bank.dto.request.ContactRequest;
import com.gxs.bank.model.ContactSubmission;
import com.gxs.bank.repository.ContactRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ContactService {

    private final ContactRepository contactRepository;

    public ContactSubmission submit(ContactRequest request) {
        ContactSubmission submission = ContactSubmission.builder()
                .name(request.getName())
                .email(request.getEmail())
                .subject(request.getSubject())
                .message(request.getMessage())
                .status(ContactSubmission.Status.NEW)
                .build();

        return contactRepository.save(submission);
    }

    public List<ContactSubmission> getByEmail(String email) {
        return contactRepository.findByEmailOrderByCreatedAtDesc(email);
    }

    public List<ContactSubmission> getAll() {
        return contactRepository.findAllByOrderByCreatedAtDesc();
    }
}
