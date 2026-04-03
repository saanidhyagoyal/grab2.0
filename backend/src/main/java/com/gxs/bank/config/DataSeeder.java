package com.gxs.bank.config;

import com.gxs.bank.model.*;
import com.gxs.bank.repository.*;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {
    private final UserRepository userRepository;
    private final AccountRepository accountRepository;
    private final CardRepository cardRepository;
    private final LoanRepository loanRepository;
    private final FixedDepositRepository fixedDepositRepository;
    private final TransactionRepository transactionRepository;
    private final NotificationRepository notificationRepository;
    private final BeneficiaryRepository beneficiaryRepository;
    private final BillPaymentRepository billPaymentRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public void run(String... args) throws Exception {
        if (userRepository.count() > 0) return;

        // ── Employees ─────────────────────────────────────────────────────────
        createUser("Admin GXS", "admin@gxs.com", "9900000001", User.Role.EMPLOYEE, User.EmployeeRole.ADMIN, User.KycStatus.VERIFIED);
        createUser("Jane Maker", "maker@gxs.com", "9900000002", User.Role.EMPLOYEE, User.EmployeeRole.MAKER, User.KycStatus.VERIFIED);
        createUser("John Checker", "checker@gxs.com", "9900000003", User.Role.EMPLOYEE, User.EmployeeRole.CHECKER, User.KycStatus.VERIFIED);

        // ── Customer 1: Rahul Sharma — Full verified, rich data ───────────────
        User rahul = createUser("Rahul Sharma", "rahul@gxs.com", "9876543210", User.Role.CUSTOMER, null, User.KycStatus.VERIFIED);
        // Enrich profile
        rahul.setDateOfBirth(LocalDate.of(1992, 6, 15));
        rahul.setGender(User.Gender.MALE);
        rahul.setAddress("42, Jalan Bukit Merah, #08-12");
        rahul.setCity("Singapore");
        rahul.setState("Central");
        rahul.setPincode("150042");
        rahul.setPanNumber("ABCRS1234K");
        rahul.setAadhaarLast4("7890");
        rahul.setNomineeName("Sneha Sharma");
        rahul.setNomineeRelation("Spouse");
        userRepository.save(rahul);

        SavingsAccount rahulAcc = createAccount(rahul, "100010000001", new BigDecimal("500000.00"));

        // Cards (ACTIVE — already approved)
        createCard(rahul, "4820", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.ACTIVE, null);
        createCard(rahul, "9234", Card.CardType.CREDIT, Card.CardNetwork.MASTERCARD, Card.Status.ACTIVE, new BigDecimal("200000"));

        // Loan — active personal loan
        createLoan(rahul, Loan.LoanType.PERSONAL, new BigDecimal("150000"), new BigDecimal("1.08"), 24, "Home Renovation", Loan.Status.ACTIVE);

        // Fixed Deposit
        createFD(rahul, rahulAcc, new BigDecimal("100000"), new BigDecimal("7.00"), 24, "FD100001");

        // Transactions
        createTxn(rahulAcc, Transaction.Type.SALARY_CREDIT, "75000.00", "Salary Credit - TechCorp India", Transaction.Channel.NET_BANKING, "575000.00");
        createTxn(rahulAcc, Transaction.Type.BILL_PAYMENT, "2450.00", "Electricity Bill - BESCOM", Transaction.Channel.MOBILE, "572550.00");
        createTxn(rahulAcc, Transaction.Type.TRANSFER_OUT, "25000.00", "Transfer to Sneha Sharma", Transaction.Channel.NEFT, "547550.00");
        createTxn(rahulAcc, Transaction.Type.ATM_WITHDRAWAL, "10000.00", "ATM Withdrawal - Koramangala ATM", Transaction.Channel.ATM, "537550.00");
        createTxn(rahulAcc, Transaction.Type.CREDIT, "15000.00", "Refund from Amazon", Transaction.Channel.NET_BANKING, "552550.00");
        createTxn(rahulAcc, Transaction.Type.POS_PURCHASE, "3800.00", "Swiggy - Food Order", Transaction.Channel.MOBILE, "548750.00");
        createTxn(rahulAcc, Transaction.Type.TRANSFER_IN, "5000.00", "Received from Priya Patel", Transaction.Channel.IMPS, "553750.00");

        // Beneficiaries for Rahul
        createBeneficiary(rahul, "Sneha Sharma", "100010000003", "GXSB0000001", "GXS Bank", "Wife");
        createBeneficiary(rahul, "Priya Patel", "100010000007", "GXSB0000001", "GXS Bank", "Friend");

        // Bill payment history for Rahul
        createBillPayment(rahul, "SP Group", BillPayment.BillerCategory.ELECTRICITY, "ELEC2023001", new BigDecimal("245.80"), rahulAcc);
        createBillPayment(rahul, "Singapore Power Gas", BillPayment.BillerCategory.GAS, "GAS2023001", new BigDecimal("68.50"), rahulAcc);
        createBillPayment(rahul, "PUB Water", BillPayment.BillerCategory.WATER, "WTR2023001", new BigDecimal("32.10"), rahulAcc);
        createBillPayment(rahul, "Singtel Broadband", BillPayment.BillerCategory.BROADBAND, "BB2023001", new BigDecimal("89.00"), rahulAcc);

        // Notifications
        createNotif(rahul, "Salary Credited", "S$75,000 has been credited to your account ending 0001.", Notification.Type.TRANSACTION, false);
        createNotif(rahul, "Loan EMI Due", "Your Personal Loan EMI of S$6,901 is due on 5th April 2026.", Notification.Type.LOAN, false);
        createNotif(rahul, "KYC Verified", "Congratulations! Your KYC has been successfully verified.", Notification.Type.KYC, true);
        createNotif(rahul, "New Offer", "Earn 5x reward points on dining this month with your Credit Card.", Notification.Type.PROMOTION, true);
        createNotif(rahul, "Bill Payment Successful", "Electricity bill for S$245.80 paid successfully to SP Group.", Notification.Type.TRANSACTION, true);

        // ── Customer 2: Unverified — just registered ──────────────────────────
        User u2 = createUser("Arjun Mehta", "unverified@gxs.com", "9876500002", User.Role.CUSTOMER, null, User.KycStatus.UNVERIFIED);
        u2.setOnboardingStatus(User.OnboardingStatus.ACCOUNT_CREATED);
        userRepository.save(u2);
        createNotif(u2, "Welcome to GXS Bank!", "Please complete your KYC to unlock all banking features.", Notification.Type.KYC, false);

        // ── Customer 3: KYC Pending Review ────────────────────────────────────
        User u3 = createUser("Sneha Sharma", "pending@gxs.com", "9876500003", User.Role.CUSTOMER, null, User.KycStatus.PENDING_REVIEW);
        u3.setDateOfBirth(LocalDate.of(1995, 3, 22));
        u3.setGender(User.Gender.FEMALE);
        u3.setAddress("88 Bedok North Road, #05-21");
        u3.setCity("Singapore");
        u3.setState("East");
        u3.setPincode("460088");
        userRepository.save(u3);
        createAccount(u3, "100010000003", new BigDecimal("15000.00"));
        createNotif(u3, "KYC Under Review", "Your documents are being verified. This usually takes 2-3 business days.", Notification.Type.KYC, false);

        // ── Customer 4: KYC Rejected ──────────────────────────────────────────
        User u4 = createUser("Vikram Singh", "rejected@gxs.com", "9876500004", User.Role.CUSTOMER, null, User.KycStatus.REJECTED);
        u4.setDateOfBirth(LocalDate.of(1988, 11, 7));
        u4.setGender(User.Gender.MALE);
        userRepository.save(u4);
        createAccount(u4, "100010000004", new BigDecimal("5000.00"));
        createNotif(u4, "KYC Rejected", "Your KYC submission was rejected. Please re-upload clear, valid documents.", Notification.Type.KYC, false);
        createNotif(u4, "Action Required", "Your account has limited access due to KYC failure. Please resubmit.", Notification.Type.SYSTEM, false);

        // ── Customer 5: Verified with pending loan ────────────────────────────
        User u5 = createUser("Kavita Nair", "loanpending@gxs.com", "9876500005", User.Role.CUSTOMER, null, User.KycStatus.VERIFIED);
        u5.setDateOfBirth(LocalDate.of(1990, 8, 14));
        u5.setGender(User.Gender.FEMALE);
        u5.setAddress("12 Tampines Street 45, #10-08");
        u5.setCity("Singapore");
        u5.setState("East");
        u5.setPincode("520012");
        u5.setPanNumber("DEFKN5678L");
        u5.setAadhaarLast4("3456");
        userRepository.save(u5);
        SavingsAccount acc5 = createAccount(u5, "100010000005", new BigDecimal("80000.00"));
        createCard(u5, "5511", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.ACTIVE, null);
        createLoan(u5, Loan.LoanType.HOME, new BigDecimal("2500000"), new BigDecimal("8.50"), 240, "Purchase of 2BHK apartment", Loan.Status.PENDING);
        createTxn(acc5, Transaction.Type.SALARY_CREDIT, "60000.00", "Salary Credit", Transaction.Channel.NET_BANKING, "140000.00");
        createTxn(acc5, Transaction.Type.BILL_PAYMENT, "1800.00", "Broadband Bill - Airtel", Transaction.Channel.MOBILE, "138200.00");
        createNotif(u5, "Loan Application Received", "Your Home Loan application for S$2,500,000 is under review.", Notification.Type.LOAN, false);

        // ── Customer 6: Verified with frozen card ─────────────────────────────
        User u6 = createUser("Rohan Gupta", "frozen@gxs.com", "9876500006", User.Role.CUSTOMER, null, User.KycStatus.VERIFIED);
        u6.setDateOfBirth(LocalDate.of(1994, 1, 30));
        u6.setGender(User.Gender.MALE);
        u6.setAddress("55 Ang Mo Kio Avenue 3, #07-15");
        u6.setCity("Singapore");
        u6.setState("Central");
        u6.setPincode("560055");
        userRepository.save(u6);
        SavingsAccount acc6 = createAccount(u6, "100010000006", new BigDecimal("25000.00"));
        createCard(u6, "7722", Card.CardType.DEBIT, Card.CardNetwork.VISA, Card.Status.FROZEN, null);
        createCard(u6, "4433", Card.CardType.CREDIT, Card.CardNetwork.MASTERCARD, Card.Status.ACTIVE, new BigDecimal("100000"));
        createFD(u6, acc6, new BigDecimal("50000"), new BigDecimal("6.50"), 12, "FD100002");
        createTxn(acc6, Transaction.Type.TRANSFER_IN, "25000.00", "Received from Rahul Sharma", Transaction.Channel.IMPS, "50000.00");
        createNotif(u6, "Card Frozen", "Your Debit Card ending 7722 has been frozen as requested.", Notification.Type.CARD, true);

        // ── Customer 7: New user, zero balance ────────────────────────────────
        User u7 = createUser("Priya Patel", "new@gxs.com", "9876500007", User.Role.CUSTOMER, null, User.KycStatus.VERIFIED);
        u7.setDateOfBirth(LocalDate.of(1997, 5, 10));
        u7.setGender(User.Gender.FEMALE);
        userRepository.save(u7);
        createAccount(u7, "100010000007", BigDecimal.ZERO);
        createNotif(u7, "Account Opened!", "Welcome to GXS Bank. Your savings account is ready to use.", Notification.Type.SYSTEM, false);

        System.out.println("✅ Seeded database with 7 customer + 3 employee accounts, transactions, loans, FDs, bills, beneficiaries, and notifications.");
    }

    private User createUser(String name, String email, String phone, User.Role role, User.EmployeeRole erole, User.KycStatus kyc) {
        User u = User.builder()
                .fullName(name)
                .email(email)
                .phone(phone)
                .passwordHash(passwordEncoder.encode("password"))
                .role(role)
                .employeeRole(erole)
                .kycStatus(kyc)
                .onboardingStatus(kyc == User.KycStatus.VERIFIED ? User.OnboardingStatus.FULLY_ONBOARDED
                        : kyc == User.KycStatus.PENDING_REVIEW ? User.OnboardingStatus.KYC_SUBMITTED
                        : User.OnboardingStatus.ACCOUNT_CREATED)
                .build();
        return userRepository.save(u);
    }

    private SavingsAccount createAccount(User user, String accNo, BigDecimal balance) {
        SavingsAccount s = SavingsAccount.builder()
                .user(user)
                .accountNumber(accNo)
                .balance(balance)
                .interestRate(new BigDecimal("4.0"))
                .dailyWithdrawalLimit(new BigDecimal("100000"))
                .monthlyTransferLimit(new BigDecimal("1000000"))
                .status(SavingsAccount.Status.ACTIVE)
                .accountType(SavingsAccount.AccountType.SAVINGS)
                .ifscCode("GXSB0000001")
                .branchName("GXS Digital Branch")
                .isUpiEnabled(true)
                .isMobileBankingEnabled(true)
                .build();
        return accountRepository.save(s);
    }

    private void createCard(User user, String last4, Card.CardType type, Card.CardNetwork network, Card.Status status, BigDecimal creditLimit) {
        Card c = Card.builder()
                .user(user)
                .cardNumberLast4(last4)
                .cardHolderName(user.getFullName().toUpperCase())
                .cardType(type)
                .status(status)
                .cardNetwork(network)
                .creditLimit(creditLimit != null ? creditLimit : BigDecimal.ZERO)
                .currentBalance(BigDecimal.ZERO)
                .cashbackEarned(new BigDecimal("0.00"))
                .dailyLimit(new BigDecimal("50000"))
                .monthlyLimit(new BigDecimal("500000"))
                .expiryDate(LocalDate.now().plusYears(5))
                .isOnlineEnabled(true)
                .isContactlessEnabled(true)
                .isInternationalEnabled(false)
                .build();
        cardRepository.save(c);
    }

    private void createLoan(User user, Loan.LoanType type, BigDecimal amount, BigDecimal rate, int tenure, String name, Loan.Status status) {
        // Monthly EMI: P*r*(1+r)^n / ((1+r)^n -1)  where r = rate/1200
        BigDecimal monthlyRate = rate.divide(new BigDecimal("1200"), 10, java.math.RoundingMode.HALF_UP);
        double r = monthlyRate.doubleValue();
        double emi = amount.doubleValue() * r * Math.pow(1 + r, tenure) / (Math.pow(1 + r, tenure) - 1);
        BigDecimal monthlyPayment = BigDecimal.valueOf(Math.round(emi * 100) / 100.0);

        Loan loan = Loan.builder()
                .user(user)
                .loanType(type)
                .loanName(name)
                .amount(amount)
                .outstandingAmount(amount)
                .interestRate(rate)
                .tenureMonths(tenure)
                .monthlyPayment(monthlyPayment)
                .totalEmis(tenure)
                .emisPaid(status == Loan.Status.ACTIVE ? 2 : 0)
                .nextEmiDate(LocalDate.now().plusMonths(1).withDayOfMonth(5))
                .status(status)
                .build();
        loanRepository.save(loan);
    }

    private void createFD(User user, SavingsAccount account, BigDecimal principal, BigDecimal rate, int tenure, String fdNumber) {
        BigDecimal interest = principal.multiply(rate)
                .multiply(BigDecimal.valueOf(tenure))
                .divide(new BigDecimal("1200"), 2, java.math.RoundingMode.HALF_UP);

        FixedDeposit fd = FixedDeposit.builder()
                .user(user)
                .sourceAccount(account)
                .principalAmount(principal)
                .interestRate(rate)
                .tenureMonths(tenure)
                .maturityAmount(principal.add(interest))
                .maturityDate(LocalDate.now().plusMonths(tenure))
                .autoRenew(false)
                .fdNumber(fdNumber)
                .status(FixedDeposit.Status.ACTIVE)
                .build();
        fixedDepositRepository.save(fd);
    }

    private void createTxn(SavingsAccount account, Transaction.Type type, String amount, String description, Transaction.Channel channel, String balanceAfter) {
        Transaction txn = Transaction.builder()
                .account(account)
                .type(type)
                .amount(new BigDecimal(amount))
                .description(description)
                .balanceAfter(new BigDecimal(balanceAfter))
                .referenceNumber("GXS" + System.nanoTime())
                .channel(channel)
                .txnStatus(Transaction.TxnStatus.SUCCESS)
                .build();
        transactionRepository.save(txn);
    }

    private void createNotif(User user, String title, String message, Notification.Type type, boolean isRead) {
        Notification notif = Notification.builder()
                .user(user)
                .title(title)
                .message(message)
                .type(type)
                .isRead(isRead)
                .createdAt(LocalDateTime.now().minusHours((long)(Math.random() * 72)))
                .build();
        notificationRepository.save(notif);
    }

    private void createBeneficiary(User user, String name, String accountNumber, String ifscCode, String bankName, String nickname) {
        Beneficiary b = Beneficiary.builder()
                .user(user)
                .beneficiaryName(name)
                .accountNumber(accountNumber)
                .ifscCode(ifscCode)
                .bankName(bankName)
                .isVerified(true)
                .build();
        beneficiaryRepository.save(b);
    }

    private void createBillPayment(User user, String billerName, BillPayment.BillerCategory category, String accountNumber, BigDecimal amount, SavingsAccount account) {
        BillPayment bp = BillPayment.builder()
                .user(user)
                .billerName(billerName)
                .billerCategory(category)
                .billerAccountNumber(accountNumber)
                .amount(amount)
                .status(BillPayment.Status.SUCCESS)
                .transactionRef("BP-GXS-" + System.nanoTime())
                .build();
        billPaymentRepository.save(bp);
    }
}
