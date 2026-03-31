package com.gxs.bank.repository;

import com.gxs.bank.model.ContactSubmission;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface ContactRepository extends JpaRepository<ContactSubmission, UUID> {
    List<ContactSubmission> findByEmailOrderByCreatedAtDesc(String email);
    List<ContactSubmission> findAllByOrderByCreatedAtDesc();
}
