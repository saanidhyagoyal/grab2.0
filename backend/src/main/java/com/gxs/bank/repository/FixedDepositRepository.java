package com.gxs.bank.repository;

import com.gxs.bank.model.FixedDeposit;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface FixedDepositRepository extends JpaRepository<FixedDeposit, UUID> {
    List<FixedDeposit> findByUserId(UUID userId);
}
