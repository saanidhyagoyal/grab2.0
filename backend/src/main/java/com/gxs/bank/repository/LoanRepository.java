package com.gxs.bank.repository;

import com.gxs.bank.model.Loan;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.UUID;

@Repository
public interface LoanRepository extends JpaRepository<Loan, UUID> {
    List<Loan> findByUserId(UUID userId);
    List<Loan> findByStatus(Loan.Status status);
    List<Loan> findByUserIdAndStatus(UUID userId, Loan.Status status);
    long countByStatus(Loan.Status status);
}
