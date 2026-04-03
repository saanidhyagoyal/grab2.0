package com.gxs.bank.repository;

import com.gxs.bank.model.SavingsAccount;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface AccountRepository extends JpaRepository<SavingsAccount, UUID> {
    List<SavingsAccount> findByUserId(UUID userId);
    Optional<SavingsAccount> findByAccountNumber(String accountNumber);
    boolean existsByAccountNumber(String accountNumber);
    List<SavingsAccount> findByUserIdAndAccountType(UUID userId, SavingsAccount.AccountType accountType);
    List<SavingsAccount> findByStatus(SavingsAccount.Status status);
}
