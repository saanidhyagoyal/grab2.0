package com.gxs.bank.repository;

import com.gxs.bank.model.BillPayment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface BillPaymentRepository extends JpaRepository<BillPayment, UUID> {
    List<BillPayment> findByUserId(UUID userId);
}
