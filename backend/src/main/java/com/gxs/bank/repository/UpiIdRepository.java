package com.gxs.bank.repository;

import com.gxs.bank.model.UpiId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface UpiIdRepository extends JpaRepository<UpiId, UUID> {
    List<UpiId> findByUserId(UUID userId);
}
